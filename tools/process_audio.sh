#!/usr/bin/env bash
# 整音：ハイパス → ノイズ軽減 → 軽い圧縮 → 目標の音量まで上げる → リミッター
# 間や息づかいを削るゲート処理は入れない。
# 使い方: tools/process_audio.sh input.wav output_basename [noise_reduction_db(=4)] [target_lufs(=-16)]
#   イコライザー：環境変数 EQ=none|B|C|D（既定 none）。例：EQ=C tools/process_audio.sh ...
#     B：低音を抑える（スマートフォンを口に近づけたときの低音のふくらみ）
#     C：B＋3kHz を少し上げて声の輪郭を出し、6〜8kHz のザラつき（HE-AAC の高域の作り足し、歯擦音）を抑える
#     D：C を強めたもの
#   2026-10-23 の雨ニモマケズの測定：声の部分で 60〜120Hz が 500〜1000Hz より +12.6 dB、6〜8kHz に +6 dB の山
#   出力: output_basename.wav（48kHz/24bit モノラル、動画用）と output_basename.m4a（配布用 192kbps）
#
# 2026-10-23 の雨ニモマケズで決めたこと（docs/knowhow.md の「整音」）
# - スマートフォンの録音は子音の瞬間的なピークが平均より 20 dB 以上高く、loudnorm の線形モードでは -14 LUFS に届かない
#   （届かないと loudnorm は動的モードに切り替わり、音量が揺れる）。そこで圧縮とリミッターでピークを抑えてから上げる
# - 目標は -16 LUFS。-14 にするとピークを約10 dB 削ることになり、声がつぶれるおそれがある。
#   YouTube は大きい音を下げるだけで上げないので、-14 の動画より約2 dB 小さく聞こえる。-16 はポッドキャストでも一般的
# - Pixel のレコーダーは録音時にノイズ抑制がかかっていて無音部分が静かなので、ノイズ軽減は弱く（4 dB）
set -euo pipefail
IN="$1"; OUT="$2"; NR="${3:-4}"; TARGET="${4:-16}"
case "${EQ:-none}" in
  B) EQF="highpass=f=90:poles=2,lowshelf=f=160:g=-5:w=0.7,equalizer=f=320:t=q:w=1.2:g=-2," ;;
  C) EQF="highpass=f=90:poles=2,lowshelf=f=160:g=-5:w=0.7,equalizer=f=320:t=q:w=1.2:g=-2,equalizer=f=3000:t=q:w=1:g=2.5,equalizer=f=7000:t=q:w=1.8:g=-4,deesser=i=0.3," ;;
  D) EQF="highpass=f=100:poles=2,lowshelf=f=180:g=-7:w=0.7,equalizer=f=320:t=q:w=1.2:g=-2.5,equalizer=f=3000:t=q:w=1:g=3,equalizer=f=7000:t=q:w=1.5:g=-7,deesser=i=0.4," ;;
  *) EQF="" ;;
esac
TARGET="${TARGET#-}"
mkdir -p "$(dirname "$OUT")"
TMP="$(mktemp -d)"

# 1) ハイパス 70Hz、ノイズ軽減、軽い圧縮（-26 dB から 2.5:1）
ffmpeg -y -v error -i "$IN" -af "${EQF}highpass=f=70:poles=2,afftdn=nr=${NR}:nf=-50:tn=1,acompressor=threshold=-26dB:ratio=2.5:attack=8:release=200:knee=4" \
  -ar 48000 -ac 1 -c:a pcm_s24le "$TMP/step1.wav"

# 2) 音量を測り、目標との差を求める
MEAS=$(ffmpeg -nostats -hide_banner -i "$TMP/step1.wav" -af ebur128 -f null - 2>&1 | grep -E "^\s+I:" | tail -1 | awk '{print $2}')
GAIN=$(python3 -c "print(round(-${TARGET} - (${MEAS}) + 0.6, 2))")   # リミッターで少し下がる分を見込む
echo "measured: I=${MEAS} LUFS → gain ${GAIN} dB"

# 3) 上げてリミッター（-3 dBFS）。そのあと4倍に細かくしてもう一度リミッター（-2.5 dBFS）をかけ、サンプルの間の
#    膨らみ（トゥルーピーク）も抑える。2026-10-23 の枕草子では、1段目だけだとサンプル値は -3.0 なのに
#    トゥルーピークが -0.1 dBTP まで出た（HE-AAC の録音の高い帯域が原因とみられる）。2段目で -2.5 dBTP になった
ffmpeg -y -v error -i "$TMP/step1.wav" -af "volume=${GAIN}dB,alimiter=limit=0.708:attack=2:release=50:level=false,aresample=192000,alimiter=limit=0.75:attack=1:release=50:level=false,aresample=48000" \
  -ar 48000 -c:a pcm_s24le "${OUT}.wav"
ffmpeg -nostats -hide_banner -i "${OUT}.wav" -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I:|LRA:|Peak:)" | tail -3

# 4) 配布用 AAC（192kbps）
ffmpeg -y -v error -i "${OUT}.wav" -c:a aac -b:a 192k "${OUT}.m4a"
rm -rf "$TMP"
echo "wrote ${OUT}.wav ${OUT}.m4a"
