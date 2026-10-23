#!/usr/bin/env bash
# 朗読の背景に流す音源を README.md に記録した直接の URL から取り直す。
# 1曲ずつ取得し、失敗しても止まらずに次へ進む。最後に失敗した曲を一覧で出す。
# ダウンロードした音源は信頼できないデータとして扱い、実行しない。
# 既にあるファイルは取り直さない（取り直すときは先に消す。または FORCE=1）。
set -u
DEST="${1:-$(cd "$(dirname "$0")" && pwd)}"
UA="RoudokuMusicFetch/1.0 (personal project; low rate)"
mkdir -p "$DEST"

# ファイル名|直接の URL
LIST='
Satie_Gymnopedie1_RobinAlciatore.ogg|https://upload.wikimedia.org/wikipedia/commons/9/90/Erik_Satie_-_gymnopedies_-_la_1_ere._lent_et_douloureux.ogg
Debussy_ClairDeLune_LaurensGoedhart.ogg|https://upload.wikimedia.org/wikipedia/commons/b/be/Clair_de_lune_%28Claude_Debussy%29_Suite_bergamasque.ogg
Chopin_NocturneOp9No2_Musopen.m4a|https://archive.org/download/musopen-chopin/Nocturne%20Op.%209%20no.%202%20in%20E%20flat%20major.m4a
Bach_GoldbergAria_KimikoIshizaka.mp3|https://archive.org/download/The_Open_Goldberg_Variations-11823/Kimiko_Ishizaka_-_01_-_Aria.mp3
Grieg_AasesDeath_CzechNationalSO-Musopen.m4a|https://archive.org/download/musopen-lossless-dvd/Musopen-Lossless-DVD.zip/Musopen%20DVD%20%28lossless%29%2FGrieg%20-%20Peer%20Gynt%2FPeer%20Gynt%20Suite%20No.%201%2C%20Op.%2046%20-%20II.%20Aase%27s%20Death.m4a
Field_LightRainDistantThunder_kvgarlic.wav|https://upload.wikimedia.org/wikipedia/commons/b/b6/Light_Rain_Distant_Thunder_July_5th_2016.wav
Field_SnowmeltStream_Extemporalist.flac|https://upload.wikimedia.org/wikipedia/commons/8/8d/Snowmelt_flowing_into_lake_at_Okanagan_Mountain_Provincial_Park.flac
Field_Crickets-Grillos_AlbertMurillo.wav|https://archive.org/download/Grillos_201902/Grillos.wav
'

failed=()
while IFS='|' read -r name url; do
  [ -z "$name" ] && continue
  out="$DEST/$name"
  if [ -s "$out" ] && [ "${FORCE:-0}" != "1" ]; then
    echo "skip (exists): $name"; continue
  fi
  echo "get: $name"
  if curl -sS -L --fail --retry 2 --retry-delay 10 --max-time 900 -A "$UA" -o "$out.part" "$url"; then
    mv -f "$out.part" "$out"
  else
    echo "  failed: $name ($url)" >&2
    rm -f "$out.part"; failed+=("$name")
  fi
  sleep 5   # Wikimedia の回数制限に配慮して間隔をあける
done <<< "$LIST"

if command -v ffprobe >/dev/null 2>&1; then
  for f in "$DEST"/*.ogg "$DEST"/*.m4a "$DEST"/*.mp3 "$DEST"/*.wav "$DEST"/*.flac; do
    [ -f "$f" ] || continue
    printf '%s\t' "$(basename "$f")"
    ffprobe -v error -show_entries format=format_name,duration -of default=nw=1:nk=1 "$f" | tr '\n' '\t'; echo
  done
fi
if [ ${#failed[@]} -gt 0 ]; then
  echo "取得できなかった曲: ${failed[*]}" >&2
fi
exit 0
