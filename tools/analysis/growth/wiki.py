import subprocess,json,urllib.parse,time,sys
UA='RoudokuResearch/1.0 (personal research; yt narration analysis)'
def get(u):
    for k in range(4):
        r=subprocess.run(['curl','-sS','--max-time','30','-A',UA,u],capture_output=True)
        try:
            d=json.loads(r.stdout)
            if 'items' in d or d.get('type','').endswith('not_found') or 'detail' in d: return d
        except Exception: pass
        time.sleep(10*(k+1))
    return {}
def pv(title):
    t=urllib.parse.quote(title.replace(' ','_'),safe='')
    d=get(f'https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/ja.wikipedia/all-access/user/{t}/monthly/2025100100/2026093000')
    it=d.get('items'); return sum(x['views'] for x in it) if it else None
C={'地獄変':['地獄変'],'蜜柑':['蜜柑 (小説)','蜜柑 (芥川龍之介)'],'河童':['河童 (小説)','河童 (芥川龍之介)'],'駈込み訴え':['駈込み訴え'],'女生徒':['女生徒','女生徒 (小説)'],
'葉桜と魔笛':['葉桜と魔笛'],'瓶詰地獄':['瓶詰地獄'],'押絵と旅する男':['押絵と旅する男'],'外科室':['外科室'],'高野聖':['高野聖 (小説)','高野聖'],'文鳥':['文鳥 (小説)','文鳥 (夏目漱石)'],
'名人伝':['名人伝'],'どんぐりと山猫':['どんぐりと山猫'],'猫の事務所':['猫の事務所'],'グスコーブドリの伝記':['グスコーブドリの伝記'],'でんでんむしのかなしみ':['でんでんむしのかなしみ'],
'おじいさんのランプ':['おじいさんのランプ'],'一握の砂':['一握の砂'],'山椒大夫':['山椒大夫'],'たけくらべ':['たけくらべ'],
'枕草子':['枕草子'],'トロッコ':['トロッコ (小説)','トロッコ (芥川龍之介)'],'野ばら':['野ばら (小説)','野ばら (小川未明)'],'桜の森の満開の下':['桜の森の満開の下'],'耳なし芳一':['耳なし芳一'],'風の又三郎':['風の又三郎']}
out={}
for w,ts in C.items():
    for t in ts:
        n=pv(t); time.sleep(6)
        if n: out[w]=dict(article=t,views12=n); break
    print(w,out.get(w),flush=True)
    json.dump(out,open(sys.argv[1],'w',encoding='utf-8'),ensure_ascii=False,indent=1)
