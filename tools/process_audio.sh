#!/usr/bin/env bash
# 整音：ノイズ軽減 → 高域/低域の整理 → 2パスのラウドネス正規化（YouTube 向け -14 LUFS）
# 間や息づかいを削るゲート処理は入れない。
# 使い方: tools/process_audio.sh input.wav output_basename [noise_reduction_db(=12)]
#   出力: output_basename.wav（48kHz/24bit、動画用）と output_basename.m4a（配布用）
set -euo pipefail
IN="$1"; OUT="$2"; NR="${3:-12}"
mkdir -p "$(dirname "$OUT")"
TARGET_I=-14; TARGET_TP=-1.0; TARGET_LRA=11

TMP="$(mktemp -d)"
# 1) ノイズ軽減（afftdn: FFT ノイズ低減。nr=低減量 dB、nf=ノイズフロア推定 dBFS、tn=ノイズ追従）
#    ハイパス 70Hz で机やエアコンの低い唸りを、ローパスはかけない（息づかいの質感を残す）
ffmpeg -y -v error -i "$IN" -af "highpass=f=70:poles=2,afftdn=nr=${NR}:nf=-50:tn=1" -ar 48000 -ac 1 -c:a pcm_s24le "$TMP/step1.wav"

# 2) ラウドネス計測（1パス目）
STATS=$(ffmpeg -nostats -hide_banner -i "$TMP/step1.wav" -af "loudnorm=I=${TARGET_I}:TP=${TARGET_TP}:LRA=${TARGET_LRA}:print_format=json" -f null - 2>&1 | sed -n '/{/,/}/p')
g() { echo "$STATS" | grep "\"$1\"" | sed 's/.*: *"\([^"]*\)".*/\1/'; }
II=$(g input_i); ITP=$(g input_tp); ILRA=$(g input_lra); ITH=$(g input_thresh); OFF=$(g target_offset)
echo "measured: I=${II} LUFS, TP=${ITP} dBTP, LRA=${ILRA}, thresh=${ITH}, offset=${OFF}"

# 3) ラウドネス正規化（2パス目、linear=true で可能なら線形ゲインのみ）
ffmpeg -y -v error -i "$TMP/step1.wav" -af "loudnorm=I=${TARGET_I}:TP=${TARGET_TP}:LRA=${TARGET_LRA}:measured_I=${II}:measured_TP=${ITP}:measured_LRA=${ILRA}:measured_thresh=${ITH}:offset=${OFF}:linear=true:print_format=summary" -ar 48000 -c:a pcm_s24le "${OUT}.wav" 2>&1 | grep -E "Output Integrated|Output True Peak|Output LRA|Normalization Type" || true

# 4) 配布用 AAC（192kbps）
ffmpeg -y -v error -i "${OUT}.wav" -c:a aac -b:a 192k "${OUT}.m4a"
rm -rf "$TMP"
echo "wrote ${OUT}.wav ${OUT}.m4a"
