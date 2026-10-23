"""作品ごとに YouTube を検索する（内部 API）。作業フォルダで: python3 tools/analysis/growth/run_search.py search_all.jsonl
手順: run_search.py → q1.py（videos_all.csv）→ chan.py（チャンネル情報）→ q1.py を再実行 → q1c.py（指標）→ q2.py（小さなチャンネル）→ q3.py（チャンネル単位）。
chan.py: python3 chan.py chids.txt chan_a.jsonl [rev]（chids.txt は朗読動画のチャンネル ID の一覧）。chanlist.py: 全動画の一覧（宇宙・AI の比較）。
分析と判断は docs/growth/consult-02-data.md（2026-10-23）。"""
import json, os, sys, time
from search import search
from works import OLD, NEW
out = sys.argv[1]
done=set()
if os.path.exists(out):
    for l in open(out,encoding='utf-8'): done.add(json.loads(l)['work'])
with open(out,'a',encoding='utf-8') as f:
    for w,a in OLD+NEW:
        if w in done: continue
        q=f'{w} {a} 朗読'.replace('  ',' ')
        for tries in range(3):
            try:
                est, rows = search(q, 60); break
            except Exception as e:
                print('err',w,e,flush=True); time.sleep(30); est,rows=None,[]
        f.write(json.dumps(dict(work=w,author=a,query=q,est=est,rows=rows,new=(w,a) in NEW),ensure_ascii=False)+'\n'); f.flush()
        print(w, est, len(rows), flush=True); time.sleep(1.5)
