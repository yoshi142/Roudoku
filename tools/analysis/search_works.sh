#!/usr/bin/env bash
# works.tsv の各作品について YouTube を検索し、上位40本を search.jsonl に書く（作業フォルダで実行）
# 使い方: bash search_works.sh works.tsv
set -u
: > search.jsonl
while IFS=$'\t' read -r w a wiki; do
  q="$w $a 朗読"; [ "$a" = "作者不詳" ] && q="$w 朗読"
  yt-dlp --flat-playlist -j --extractor-args "youtube:lang=ja" "ytsearch40:$q" 2>/dev/null | python3 -I -c "
import sys,json
w=sys.argv[1]
for i,l in enumerate(sys.stdin):
    d=json.loads(l); print(json.dumps(dict(work=w,rank=i+1,id=d['id'],title=d.get('title'),ch=d.get('channel'),chid=d.get('channel_id'),views=d.get('view_count') or 0,dur=d.get('duration') or 0),ensure_ascii=False))" "$w" >> search.jsonl
  sleep 1
done < "$1"
