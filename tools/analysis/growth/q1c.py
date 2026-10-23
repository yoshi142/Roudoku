import os, pandas as pd, numpy as np, json
from scipy.stats import spearmanr
W='./'
R=os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../docs/research/data/')
pd.set_option('display.width',250); pd.set_option('display.max_rows',100)
v=pd.read_csv(W+'videos_all.csv'); r=v[v.rodoku].copy()
wk=pd.read_csv(R+'analysis_works_2026-10-23.csv').set_index('work'); wiki=wk.wiki.to_dict()
for k,x in json.load(open(W+'wiki_new.json',encoding='utf-8')).items():
    if x and x['views12'] and x['views12']>500 and pd.isna(wiki.get(k,np.nan)): wiki[k]=x['views12']
small=r[r.subs<10000]; rs=small[small.age<=3*365]
g=r.groupby('work')
t=pd.DataFrame({'new':g.new.first(),'author':g.author.first(),'n':g.size(),'total':g.views.sum(),'flow':g.vpd365.sum(),
 'n10k':g.apply(lambda x:(x.views>=10000).sum()),'nbig':g.apply(lambda x:(x.subs>=100000).sum()),'n1y':g.apply(lambda x:(x.age<=365).sum()),
 'top_share':g.apply(lambda x:x.vpd365.max()/x.vpd365.sum()),
 'rs_n':rs.groupby('work').size(),'rs_med':rs.groupby('work').views.median(),'rs_p1k':rs.groupby('work').views.apply(lambda x:(x>=1000).mean()),
 'rs_vpd':rs.groupby('work').vpd365.median(),'min_med':g['min'].median()})
t['wiki']=t.index.map(wiki)
t['S']=t.nbig+t.n1y+1
t['G']=t.flow/t.S
t['rank']=t.G.rank(ascending=False).astype(int)
t=t.sort_values('G',ascending=False)
print(t.round(2).to_string())
m=t.rs_n>=4
print('G vs rs_med rho=%.2f, vs rs_p1k %.2f, n=%d'%(spearmanr(t.G[m],t.rs_med[m])[0],spearmanr(t.G[m],t.rs_p1k[m])[0],m.sum()))
t.to_csv(W+'q1_final.csv')
