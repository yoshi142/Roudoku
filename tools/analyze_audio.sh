#!/usr/bin/env bash
# 録音ファイルの状態を調べる（整音の前後で実行し、log.md に記録する）。
# 出力: 形式、長さ、ラウドネス（LUFS）、トゥルーピーク、暗騒音の目安、無音区間（言い直しの手がかり）
# 使い方: tools/analyze_audio.sh input.wav [silence_sec(=1.5)] [silence_threshold_dB(=-35)]
set -euo pipefail
IN="$1"; SIL="${2:-1.5}"; TH="${3:--35}"
echo "== file: $IN"
ffprobe -v error -show_entries stream=codec_name,sample_rate,channels,bits_per_raw_sample:format=duration -of default=noprint_wrappers=1 "$IN"
echo "== loudness (EBU R128)"
ffmpeg -nostats -hide_banner -i "$IN" -af ebur128=peak=true -f null - 2>&1 | grep -A 20 "Summary:" | sed 's/^ *//' | grep -E "I:|LRA:|Peak:" | head -4
echo "== level stats (astats)"
ffmpeg -nostats -hide_banner -i "$IN" -af "astats=measure_overall=Peak_level+RMS_level+Noise_floor+RMS_trough:measure_perchannel=none" -f null - 2>&1 | grep -E "Peak level|RMS level|Noise floor|RMS trough" | sed 's/^.*\] //'
echo "== silences >= ${SIL}s (threshold ${TH}dB)"
ffmpeg -nostats -hide_banner -i "$IN" -af "silencedetect=noise=${TH}dB:d=${SIL}" -f null - 2>&1 | grep -E "silence_(start|end)" | sed 's/^.*\] //'
