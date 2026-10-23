import subprocess,json,urllib.parse,time
UA='RoudokuResearch/1.0 (personal research; yt narration analysis)'
def get(u):
    for k in range(5):
        r=subprocess.run(['curl','-sS','--max-time','30','-A',UA,u],capture_output=True)
        try: return json.loads(r.stdout)
        except Exception: time.sleep(10*(k+1))
    return {}
def pv(title):
    t=urllib.parse.quote(title.replace(' ','_'),safe='')
    d=get(f'https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/ja.wikipedia/all-access/user/{t}/monthly/2025100100/2026093000')
    it=d.get('items'); return sum(x['views'] for x in it) if it else None
try:
    out=json.load(open('wiki.json',encoding='utf-8'))
except FileNotFoundError:
    out={}
works=[l.rstrip('\n').split('\t') for l in open('works.tsv',encoding='utf-8')]
for w,a,wiki in works:
    out.setdefault(w,{'article':None,'views12':None})
cands={'杜子春':['杜子春 (芥川龍之介)','杜子春 (小説)','杜子春'],'トロッコ':['トロッコ (芥川龍之介)','トロッコ (小説)'],'藪の中':['藪の中'],'銀河鉄道の夜':['銀河鉄道の夜'],'手袋を買いに':['手袋を買いに'],'夢十夜':['夢十夜'],'檸檬':['檸檬 (小説)','檸檬 (梶井基次郎)'],'野ばら':['野ばら (小川未明)','野薔薇 (小川未明)'],'形':['形 (小説)'],'一房の葡萄':['一房の葡萄'],'枕草子':['枕草子'],'桜の森の満開の下':['桜の森の満開の下'],'耳なし芳一':['耳なし芳一'],'風の又三郎':['風の又三郎'],'人間椅子':['人間椅子 (小説)','人間椅子']}
for w,a,wiki in works:
    ts=cands.get(w,[wiki,w])
    if out.get(w,{}).get('views12') and w!='人間椅子': continue
    for t in ts:
        n=pv(t); time.sleep(4)
        if n and n>3000: out[w]=dict(article=t,views12=n); break
        if n and w!='人間椅子': out[w]=dict(article=t,views12=n); break
    print(w,out.get(w),flush=True)
    json.dump(out,open('wiki.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
