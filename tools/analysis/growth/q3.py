import os, pandas as pd, numpy as np, json, glob, re
from scipy.stats import spearmanr
from genre import genre
W='./'
pd.set_option('display.width',250); pd.set_option('display.max_rows',200); pd.set_option('display.max_colwidth',40)
ch={}
for g in glob.glob(W+'chan_*.jsonl'):
    for l in open(g,encoding='utf-8'):
        j=json.loads(l); ch[j['chid']]=j
ROD=re.compile(r'朗読|読み聞かせ|よみきかせ|オーディオブック|audiobook|青空文庫|音読',re.I)
rows=[]
for c,j in ch.items():
    rec=[x for x in j.get('recent',[]) if x.get('title')]
    nr=len(rec)
    rod=sum(1 for x in rec if ROD.search(x['title']) or genre(x['title'])=='文学')
    sp=sum(1 for x in rec if genre(x['title'])=='宇宙'); ai=sum(1 for x in rec if genre(x['title'])=='AI')
    ages=[x['age'] for x in rec if x.get('age') is not None]
    subs=j.get('subs') if j.get('subs') is not None else j.get('subs_h')
    rows.append(dict(chid=c,name=j.get('name'),subs=subs,n_videos=j.get('n_videos') or j.get('nvid_h'),total_views=j.get('total_views'),joined=j.get('joined'),
        n_recent=nr,rod_share=rod/nr if nr else np.nan,space=sp,ai=ai,last_age=min(ages) if ages else np.nan,
        up_1y=sum(1 for a in ages if a<=365),recent_med_views=np.median([x['views'] for x in rec if x.get('views') is not None]) if rec else np.nan,
        desc=j.get('desc','')[:200]))
c=pd.DataFrame(rows)
c['joined']=pd.to_datetime(c.joined,errors='coerce')
c['years']=(pd.Timestamp('2026-10-23')-c.joined).dt.days/365.25
c['vids_per_year']=c.n_videos/c.years.clip(lower=0.25)
c.to_csv(W+'channels.csv',index=False)
rc=c[(c.rod_share>=0.5)&c.subs.notna()&(c.n_videos>0)].copy()
print('all',len(c),'rodoku-focused',len(rc))
rc['nb']=pd.cut(rc.n_videos,[0,10,30,100,300,1000,1e6],labels=['1-10','11-30','31-100','101-300','301-1000','1001+'])
rc['yb']=pd.cut(rc.years,[0,1,2,4,7,10,30],labels=['1年未満','1-2年','2-4年','4-7年','7-10年','10年以上'])
def summ(x): return pd.Series(dict(n=len(x),subs_med=x.subs.median(),p1k=(x.subs>=1000).mean(),p10k=(x.subs>=10000).mean(),p100k=(x.subs>=100000).mean(),views_per_video=(x.total_views/x.n_videos).median()))
print(rc.groupby('nb').apply(summ).round(2))
print(rc.groupby('yb').apply(summ).round(2))
print(pd.crosstab(rc.nb,rc.yb,values=rc.subs,aggfunc='median'))
print(pd.crosstab(rc.nb,rc.yb))
print('rho subs~nvid',spearmanr(rc.subs,rc.n_videos)[0],' subs~years',spearmanr(rc.subs,rc.years,nan_policy='omit')[0], ' subs~vpy',spearmanr(rc.subs,rc.vids_per_year,nan_policy='omit')[0])
# OLS log
m=rc.dropna(subset=['years'])
m=m[(m.subs>0)]
X=np.column_stack([np.ones(len(m)),np.log10(m.n_videos),np.log10(m.years.clip(lower=0.25))])
y=np.log10(m.subs)
b,res,_,_=np.linalg.lstsq(X,y,rcond=None)
pred=X@b; r2=1-((y-pred)**2).sum()/((y-y.mean())**2).sum()
print('OLS log10 subs = %.2f + %.2f log10 nvid + %.2f log10 years ; R2=%.2f n=%d'%(b[0],b[1],b[2],r2,len(m)))
# young channels
y2=rc[rc.years<=3].sort_values('subs',ascending=False)
print(y2[['name','subs','n_videos','years','total_views','up_1y','rod_share']].head(30).to_string())
print(len(y2), (y2.subs>=1000).mean(), (y2.subs>=10000).mean())
rc.to_csv(W+'channels_rodoku.csv',index=False)
