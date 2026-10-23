import os, pandas as pd, numpy as np, json, glob, re
W='./'
pd.set_option('display.width',250); pd.set_option('display.max_colwidth',60); pd.set_option('display.max_rows',200)
v=pd.read_csv(W+'videos_all.csv'); r=v[v.rodoku].copy()
ch={}
for g in glob.glob(W+'chan_*.jsonl'):
    for l in open(g,encoding='utf-8'):
        j=json.loads(l); ch[j['chid']]=j
r['ch_nvid']=r.chid.map(lambda c: (ch.get(c) or {}).get('n_videos') or (ch.get(c) or {}).get('nvid_h'))
r['ch_joined']=pd.to_datetime(r.chid.map(lambda c:(ch.get(c) or {}).get('joined')),errors='coerce')
r['ch_years']=(pd.Timestamp('2026-10-23')-r.ch_joined).dt.days/365.25
r['post_year']=(2026.81 - r.age/365.25).round(2)
celeb=re.compile(r'江守徹|宮沢りえ|中嶋朋子|市原悦子|沢城みゆき|渡辺謙|橋爪|ブラザートム|壤晴彦|日髙徹郎|日高徹郎|国井雅比古|國井雅比古|浅沼晋太郎|近藤サト|平野啓子|阿座上洋平|南壽あさ子|窪田等|西村俊彦|岸田今日子|森本レオ|長岡輝子|寺田農|市川|仲代|声優|俳優|アナウンサー|ナレーター')
r['pro']=r.title.str.contains(celeb)
r['learn']=r.title.str.contains('音読|暗記|暗唱|小[1-6１-６]|中[1-3１-３]|教科書|テスト|覚え')
r['tag']=r.title.str.startswith('【朗読】')|r.title.str.contains('^\[朗読\]')
r['sleep']=r.title.str.contains('睡眠|寝落ち|眠れ|おやすみ|眠く')
r['subt']=r.title.str.contains('字幕|ふりがな|SUB',case=False)
r['series']=r.title.str.contains(r'[①-⑳]|第[一二三四五六七八九十0-9]+[回夜話章]|\(\d\)|（\d）|＜\d＞|<\d>|前編|後編|上\)|下\)|その[0-9一二三]')
r['lb']=pd.cut(r['min'],[0,5,15,30,60,120,10000],labels=['5分未満','5-15分','15-30分','30-60分','1-2時間','2時間以上'])
r.to_csv(W+'videos_rodoku_enriched.csv',index=False)
s=r[(r.subs<10000)&r.subs.notna()].copy()
s['hit']=s.views>=10000
print('small videos',len(s),'hits',s.hit.sum(),'channels',s[s.hit].chid.nunique(), 'works',s[s.hit].work.nunique())
agg=lambda x: pd.Series(dict(n=len(x),age_med_y=(x.age.median()/365.25),min_med=x['min'].median(),subs_med=x.subs.median(),
   ch_nvid_med=x.ch_nvid.median(),ch_years_med=x.ch_years.median(),pro=x.pro.mean(),learn=x.learn.mean(),tag=x.tag.mean(),sleep=x.sleep.mean(),subt=x.subt.mean(),series=x.series.mean(),live=x.live.mean(),
   new_work=x.new.mean()))
print(s.groupby('hit').apply(agg).T.round(2))
print(pd.crosstab(s.lb,s.hit,margins=True))
print(pd.crosstab(pd.cut(s.age/365.25,[0,1,2,3,5,8,30]),s.hit,margins=True))
print(pd.crosstab(pd.cut(s.ch_nvid,[0,10,30,100,300,1000,1e6]),s.hit,margins=True))
h=s[s.hit].sort_values('views',ascending=False)
print(h[h.age<=3*365][['work','title','ch','subs','views','pub','min','ch_nvid','ch_years']].to_string())
s.to_csv(W+'small_videos.csv',index=False)
