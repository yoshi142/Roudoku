#!/usr/bin/env python3
"""投稿日・コメントを取る動画の一覧（batch.txt）を作る。作品ごとの再生上位12本の投稿日、うち上位4本（再生5,000回以上）はコメント20件。
使い方（作業フォルダで）: python3 make_batch.py   →  batch.txt
そのあと: python3 /path/to/repo/tools/yt_innertube.py --batch batch.txt --out details.jsonl --sleep 1.2
"""
import json, collections
rows = [json.loads(l) for l in open('search.jsonl', encoding='utf-8')]
by = collections.defaultdict(list)
for r in rows:
    by[r['work']].append(r)
lines, seen = [], set()
for w, rs in by.items():
    rs = sorted(rs, key=lambda r: -r['views'])
    for i, r in enumerate(rs[:12]):
        if r['id'] in seen:
            continue
        seen.add(r['id'])
        lines.append(f"{r['id']} {20 if (i < 4 and r['views'] >= 5000) else 0}")
open('batch.txt', 'w').write('\n'.join(lines) + '\n')
print(len(lines), '本')
