# 朗読動画の分析スクリプト（2026-10-23 の分析 docs/analysis/report.md の再現用）

Ver.1.0　作成日：2026-10-23　作成：AI

分析は、作業フォルダ（リポジトリの外、例：/tmp/an/）で行う。スクリプトは作業フォルダを基準に読み書きする。大きな中間ファイル（検索結果、サムネイル画像、投稿日とコメント）はリポジトリに入れていない。要約と集計表は docs/research/data/ にある。

## 手順（上から順に。作業フォルダで実行）

```
cp tools/analysis/works.tsv .                      # 作品の一覧（作品名、作者、ウィキペディアの記事名）
bash tools/analysis/search_works.sh works.tsv      # 1. 作品ごとに YouTube を検索（search.jsonl）  依存: yt-dlp
python3 tools/analysis/prep.py                     # 2. 題名に作品名を含む動画に絞り、種類（朗読・絵本・解説）と題名の要素を付ける（videos_prep.json）
python3 tools/analysis/make_batch.py               # 3. 投稿日とコメントを取る動画の一覧（batch.txt）
python3 tools/yt_innertube.py --batch batch.txt --out details.jsonl --sleep 1.2     # 4. 投稿日、登録者数、上位コメント（回数制限があるので時間がかかる）
python3 tools/analysis/channel_subs.py             # 5. チャンネルの登録者数（chsubs_it.json）。逆順で2本並行すると早い
python3 tools/analysis/merge_channel_subs.py       #    併合（chsubs_merged.json）
python3 tools/analysis/wiki_pageviews.py           # 6. ウィキペディアの閲覧数（wiki.json。回数制限が厳しいので間隔が長い）
# サムネイル画像（mqdefault）を thm/ に保存してから:
python3 tools/analysis/thfeat.py                   # 7. サムネイルの数値（thfeat.json）  依存: opencv-python-headless
python3 tools/analysis/worktable.py                # 8. 作品ごとの表（worktable.json）
python3 tools/analysis/analyze.py                  # 9. 重回帰（analysis_out.json、analysis_df.csv）  依存: statsmodels, pandas
python3 tools/analysis/comments.py                 # 10. コメントの分類（comments_result.txt）
```

依存のインストール：`pip install yt-dlp opencv-python-headless statsmodels pandas scipy`

## 注意

- 手順6の wiki_pageviews.py は、取得できていない作品の記事名の候補を決め打ちしている。作品を増やすときは、works.tsv の3列目と、このスクリプトの候補を直す
- opencv 5 には顔検出（CascadeClassifier）がない。顔の有無は目視で見た
- YouTube の動画ページ取得は 429 や「bot ではないことを確認」で止まりやすい。yt_innertube.py と、チャンネルページの取得は通りやすかった
- 登録者数を公開していないチャンネルは 0 として扱われる。analyze.py は 0 のチャンネルを除く
- 分析の判断（倍率の読み方、限界）は docs/analysis/report.md にある
