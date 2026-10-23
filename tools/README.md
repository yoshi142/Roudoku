# tools　整音・動画化の手順

録音ファイル（原音）が `narration/trial-NN/raw/` に置かれたあと、AI が次の順で実行する。原音は上書きしない。

```
# 0) フォント（初回のみ。IPAex明朝、IPAフォントライセンス）
tools/fetch_fonts.sh

# 1) 原音の状態を記録する（形式、長さ、ラウドネス、暗騒音、長い無音）
tools/analyze_audio.sh narration/trial-01/raw/trial-01_take01.wav

# 2) 言い直しの合図（手拍子）の候補を探し、cuts.txt を書く（人が確認）
python3 tools/find_claps.py narration/trial-01/raw/trial-01_take01.wav

# 2b) 文字起こし（faster-whisper、無料・ローカル）。合図の前後で「どこから読み直したか」を決める材料にする。字幕の下書き(.srt)も出る
python3 tools/transcribe.py narration/trial-01/raw/trial-01_take01.wav --out narration/trial-01/out/transcript --model small
python3 tools/find_claps.py narration/trial-01/raw/trial-01_take01.wav > narration/trial-01/out/claps.txt
python3 tools/retake_helper.py narration/trial-01/out/transcript.tsv narration/trial-01/out/claps.txt > narration/trial-01/cuts.txt
#    → cuts.txt を人が確認・修正する

# 3) 言い直し区間を取り除く
python3 tools/apply_cuts.py narration/trial-01/raw/trial-01_take01.wav narration/trial-01/cuts.txt narration/trial-01/out/cut.wav

# 4) 整音（ノイズ軽減 → -14 LUFS / -1 dBTP に正規化）。第3引数はノイズ低減量 dB（既定 12。やりすぎると声が痩せる）
tools/process_audio.sh narration/trial-01/out/cut.wav narration/trial-01/out/trial-01_mastered 12

# 5) 処理後の状態を記録する
tools/analyze_audio.sh narration/trial-01/out/trial-01_mastered.wav

# 6) 題名入りの静止画（1920×1080）。2026-10-23 以降は v2 を使う（docs/thumbnail/README.md に例）
#    python3 tools/make_thumbnail_v2.py --bg tools/backgrounds/<背景> --title 作品名 --author 作者 --narrator "朗読　名前" --out .../thumbnail_v2.png --preview
#    以下は旧版（使わない）
python3 tools/make_thumbnail.py --title 雨ニモマケズ --author 宮沢賢治 --series 朗読 --note 青空文庫より --out narration/trial-01/out/thumbnail.png
#    やまなし（本人の指定の文言を入れる。「｜」で列を分けると文字が大きくなる）
# python3 tools/make_thumbnail.py --title "クラムボンは｜かぷかぷ笑ったよ｜やまなし" --author 宮沢賢治 --series 朗読 --note 青空文庫より --out narration/trial-02-yamanashi/out/thumbnail.png

# 7) 動画
tools/make_video.sh narration/trial-01/out/thumbnail.png narration/trial-01/out/trial-01_mastered.wav narration/trial-01/out/trial-01.mp4
```

依存：ffmpeg 6 以上、Python 3 と Pillow、NumPy、faster-whisper（`pip install faster-whisper`。初回にモデルを取得する）。すべて無料。

目安：YouTube はおおむね -14 LUFS を基準に再生音量をそろえるため、整音の目標を -14 LUFS、トゥルーピーク -1 dBTP とした。

## そのほかの道具

- tools/make_thumbnail_v2.py　サムネイル v2（調査にもとづく型）。背景の出典は tools/backgrounds/README.md
- tools/yt_research.py　YouTube の朗読動画の調査（検索、詳細、登録者数、同じ作品の上位・下位の一覧画像）。`pip install yt-dlp`
- tools/aozora_script.py　青空文庫の XHTML から台本を作る
