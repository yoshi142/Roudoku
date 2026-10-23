import json,statistics as st,collections
V=json.load(open('videos_prep.json',encoding='utf-8'))
wiki=json.load(open('wiki.json',encoding='utf-8'))
works=[l.split('\t')[0] for l in open('works.tsv',encoding='utf-8')]
rows=[]
for w in works:
    n=[r for r in V if r['work']==w and r['kind']=='narration']
    vs=sorted([r['views'] for r in n],reverse=True)
    if not vs: continue
    mins=[r['min'] for r in n if r['min']]
    top=max(n,key=lambda r:r['views'])
    rows.append(dict(work=w,wiki=wiki.get(w,{}).get('views12'),n=len(vs),total=sum(vs),top1=vs[0],top1_ch=top['ch'],top1_min=round(top['min'] or 0),
        n100k=sum(1 for v in vs if v>=100000),n10k=sum(1 for v in vs if v>=10000),median=st.median(vs),med_min=round(st.median(mins)) if mins else None,
        small=sum(1 for v in vs if v<1000)))
json.dump(rows,open('worktable.json','w',encoding='utf-8'),ensure_ascii=False)
print(f"{'作品':<14}{'ウィキ閲覧12か月':>12}{'朗読本数':>6}{'総再生':>12}{'最多':>11}{'10万超':>6}{'1万超':>6}{'中央値':>8}{'長さ中央値':>6}")
for r in sorted(rows,key=lambda r:-r['total']):
    print(f"{r['work']:<14}{(r['wiki'] or 0):>12,}{r['n']:>6}{r['total']:>12,}{r['top1']:>11,}{r['n100k']:>6}{r['n10k']:>6}{r['median']:>8,.0f}{(r['med_min'] or 0):>6}")
