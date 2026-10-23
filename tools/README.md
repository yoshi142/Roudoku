# tools　整音・動画化の手順

録音ファイル（原音）が `narration/trial-NN/raw/` に置かれたあと、AI が次の順で実行する。原音は上書きしない。

2026-10-23 からの手順（録り方：言い直しは同じ行を頭から読み直す。手拍子はしない）。処理の前に docs/knowhow.md を読む。

```
# 0) フォント（初回のみ）と依存
tools/fetch_fonts.sh
pip install faster-whisper pykakasi && pip install --use-pep517 fugashi unidic-lite

# 1) 届いた m4a を raw/ に置き、無加工の WAV も作る（元の m4a も残す）
ffmpeg -i 届いたファイル.m4a -map 0:a:0 -c:a pcm_s24le narration/trial-01/raw/trial-01_take01.wav

# 2) 読み直しの切り詰めと「、」「。」の間そろえ（台本と照合して最後の読みを残す）
python3 tools/auto_edit.py narration/trial-01/raw/trial-01_take01.wav --out narration/trial-01/out/auto --script narration/trial-01/script.md
#    → out/auto/report.md（残した読み、捨てた区間、台本との違い）を読む。直すときは phrases.tsv を書き換えて --phrases で作り直す

# 3) 整音（圧縮 → -16 LUFS → リミッター）
tools/process_audio.sh narration/trial-01/out/auto/edited.wav narration/trial-01/out/trial-01_mastered

# 3b) 字幕（台本の文字。古典は --gloss で原文の下に現代語訳）と動画用の背景
python3 tools/make_subtitles.py narration/trial-01/out/auto/timeline.json narration/trial-01/script.md --out narration/trial-01/out/subtitles [--gloss narration/trial-12-koten/script.md]
python3 tools/make_video_bg.py --bg tools/backgrounds/<背景> --zoom 1.06 --title 作品名 --author 作者 --out narration/trial-01/out/video_bg.png
python3 tools/make_reading_video.py --bg narration/trial-01/out/video_bg.png --voice narration/trial-01/out/trial-01_mastered.wav --ass narration/trial-01/out/subtitles.ass --music tools/music/<曲> --out narration/trial-01/out/trial-01.mp4

# 4) 静止画（朗読者名なし）と動画（字幕なしの旧手順）
python3 tools/make_thumbnail_v2.py --bg tools/backgrounds/<背景> --title 作品名 --author 作者 --out narration/trial-01/out/thumbnail_v2.png --preview
tools/make_video.sh narration/trial-01/out/thumbnail_v2.png narration/trial-01/out/trial-01_mastered.wav narration/trial-01/out/trial-01.mp4
```

以下は 2026-10-22 の旧手順（手拍子を合図にした切り詰め）。手拍子で録った録音にだけ使う。

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

目安：YouTube はおおむね -14 LUFS を基準に再生音量をそろえる。スマートフォンの録音は瞬間的なピークが高く、-14 まで上げると声がつぶれるおそれがあるので、2026-10-23 から目標を -16 LUFS、トゥルーピーク -1 dBTP 以下とした（docs/knowhow.md）。

## そのほかの道具

- tools/make_thumbnail_v2.py　サムネイル v2（調査にもとづく型）。背景の出典は tools/backgrounds/README.md
- tools/yt_research.py　YouTube の朗読動画の調査（検索、詳細、登録者数、同じ作品の上位・下位の一覧画像）。`pip install yt-dlp`
- tools/aozora_script.py　青空文庫の XHTML から台本を作る（散文。詩は tools/extract_poems.py と tools/poem_scripts.py）
- tools/analysis/　朗読動画の分析の再現用スクリプトと手順（README あり）
