#!/usr/bin/env bash
# 静止画 + 音声 → 1920×1080 の動画（H.264/AAC、YouTube 向け）
# 使い方: tools/make_video.sh thumbnail.png audio.wav output.mp4
set -euo pipefail
IMG="$1"; AUD="$2"; OUT="$3"
mkdir -p "$(dirname "$OUT")"
ffmpeg -y -v error -loop 1 -framerate 2 -i "$IMG" -i "$AUD" \
  -c:v libx264 -tune stillimage -preset medium -crf 20 -pix_fmt yuv420p -r 30 \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=yuv420p" \
  -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration,size -of default=noprint_wrappers=1 "$OUT"
echo "wrote $OUT"
