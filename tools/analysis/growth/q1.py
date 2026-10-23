import os, pandas as pd, numpy as np, json, glob, re, unicodedata
from scipy.stats import spearmanr
from works import names
W='./'
R=os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../docs/research/data/')
EXC = re.compile(r'解説|要約|あらすじ|考察|授業|まとめ|ゆっくり|漫画|マンガ|アニメ|歌ってみた|歌う|AI音楽|映画|ドラマ|わかる|分かる|オリジナル曲|MV|cover|カバー|ネタバレ|読書感想|感想文|紹介|レビュー|舞台|朗読劇|ミュージカル|講座|英語で|English ver|中国語|勉強法|文法|品詞|テスト対策|を語る|名著|結末|ジオラマ|新解釈|インスタントフィクション|YouTube大学|【Update版】')
def norm(s): return unicodedata.normalize('NFKC', s or '').replace(' ','').replace('　','')
EXTRA={'でんでんむしのかなしみ':['でんでん虫のかなしみ','でんでん虫の悲しみ']}
AMBIG={'形':'菊池','鼻':'芥川','初恋':'藤村','こころ':'漱石','蜜柑':'芥川','文鳥':'漱石','河童':'芥川','女生徒':'太宰','檸檬':'梶井','智恵子抄':'高村'}
rows=[]
for l in open(W+'search_all.jsonl',encoding='utf-8'):
    j=json.loads(l)
    seen=set()
    for r in j['rows']:
        if r['id'] in seen: continue
        seen.add(r['id'])
        t=norm(r['title'])
        hit=any(norm(n) in t for n in names(j['work'])+EXTRA.get(j['work'],[]))
        if j['work'] in AMBIG and AMBIG[j['work']] not in t: hit=False
        rows.append(dict(work=j['work'],author=j['author'],new=j['new'],est=j['est'],**r,rodoku=hit and not EXC.search(r['title'] or '')))
df=pd.DataFrame(rows)
# channel info
ch={}
for g in glob.glob(W+'chan_*.jsonl'):
    for l in open(g,encoding='utf-8'):
        j=json.loads(l)
        if j.get('error'): continue
        ch[j['chid']]=j
old=pd.read_csv(R+'analysis_videos_2026-10-23.csv')
oldsubs=old.groupby('ch').subs.max().to_dict()
def subs_of(r):
    c=ch.get(r.chid)
    if c:
        s=c.get('subs') if c.get('subs') is not None else c.get('subs_h')
        if s is not None: return s
        if c.get('subs_text') is None and c.get('subs_h') is None: return np.nan  # hidden
    return oldsubs.get(r.ch, np.nan)
df['subs']=df.apply(subs_of,axis=1)
df['age']=df.age_days.clip(lower=1)
df['vpd']=df.views/df.age
df['vpd365']=df.views/df.age.clip(lower=365)
df['live']=df.pub.fillna('').str.contains('配信済み')
df['min']=df.sec/60
df.to_csv(W+'videos_all.csv',index=False)
