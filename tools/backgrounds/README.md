# サムネイル用の背景画像と権利表記

方針：背景は「人の手で作られたもの」に限る。AI 生成画像は使わない。
優先順位：(1) 本人が撮った写真 (2) パブリックドメイン／CC0 の版画・写真（出典を下に記録） (3) 背景なし（文字だけ）

| ファイル | 作品 | 作者・年 | 所蔵と権利 | URL |
|----------|------|----------|------------|-----|
| met_36521_hiroshige_shono_hakuu.jpg | 東海道五十三次之内 庄野 白雨 | 歌川広重、1834〜35年 | メトロポリタン美術館、Open Access（CC0） | https://www.metmuseum.org/art/collection/search/36521 |
| met_55433_hiroshige_ohashi_yudachi.jpg | 名所江戸百景 大はしあたけの夕立 | 歌川広重、1857年 | メトロポリタン美術館、Open Access（CC0） | https://www.metmuseum.org/art/collection/search/55433 |
| met_36531_hiroshige_karasaki_yau.jpg | 近江八景之内 唐崎夜雨 | 歌川広重、1835年ごろ | メトロポリタン美術館、Open Access（CC0） | https://www.metmuseum.org/art/collection/search/36531 |
| met_54091_hokusai_crab.jpg | 蟹と稲穂（摺物） | 葛飾北斎、19世紀 | メトロポリタン美術館、Open Access（CC0） | https://www.metmuseum.org/art/collection/search/54091 |
| met_36935_hiroshige_hara_asanofuji.jpg | 東海道五十三次之内 原 朝之富士 | 歌川広重、1833〜34年ごろ | メトロポリタン美術館、Open Access（CC0） | https://www.metmuseum.org/art/collection/search/36935 |
| met_36515_hiroshige_arashiyama_sakura.jpg | 京都名所之内 あらし山満花 | 歌川広重、1834年ごろ | メトロポリタン美術館、Open Access（CC0） | https://www.metmuseum.org/art/collection/search/36515 |
| met_55997_hiroshige_yodogawa.jpg | 京都名所之内 淀川 | 歌川広重、1834年 | メトロポリタン美術館、Open Access（CC0） | https://www.metmuseum.org/art/collection/search/55997 |
| met_36530_hiroshige_katata_rakugan.jpg | 近江八景之内 堅田落雁 | 歌川広重、1835年ごろ | メトロポリタン美術館、Open Access（CC0） | https://www.metmuseum.org/art/collection/search/36530 |
| met_36545_hiroshige_kisoji_snow.jpg | 木曽路之山川 | 歌川広重、1857年 | メトロポリタン美術館、Open Access（CC0） | https://www.metmuseum.org/art/collection/search/36545 |

取得日：2026-10-23（原 朝之富士は Part 3 で追加。枕草子の動画に使用。左上の版画の題字と画面の題名が重ならないよう、make_video_bg.py --zoom 1.45 --focus 0.98,0.36 で右寄りに切り抜いた）。メトロポリタン美術館の Open Access 画像は CC0（著作権を放棄、商用利用可、表記は任意）。説明文に「背景：歌川広重『庄野 白雨』（メトロポリタン美術館所蔵、パブリックドメイン）」のように書くと、出どころが分かり信頼につながる。

探し方：Met の検索 API（https://collectionapi.metmuseum.org/public/collection/v1.1/search?q=語&hasImages=true&isPublicDomain=true）。旧 /v1/search は 2026-10-01 に廃止。
Wikimedia Commons の API はこの環境から回数制限にかかりやすい。

### 枕草子の季節ごとの背景（2026-10-23、Part 3。本人の指示：春・夏・秋・冬で背景を変える、サムネイルは春）

| 段 | 版画 | make_video_bg.py の設定（共通：--dim 0.62 --color 1.0 --center_shade 0.45） |
|----|------|------|
| 春 | あらし山満花（桜。京都は清少納言の都） | --zoom 1.2 --focus 0.47,0.4 |
| 夏 | 淀川（月夜とほととぎす） | --zoom 1.3 --focus 0.52,0.42 |
| 秋 | 堅田落雁（夕暮れの空に雁の列） | --zoom 1.38 --focus 0.58,0.42 |
| 冬 | 木曽路之山川（雪） | --zoom 1.08 --focus 0.45,0.5 |

サムネイル：あらし山満花、make_thumbnail_v2.py --zoom 1.4 --focus 0.42,0.42 --bg_bright 0.9 --bg_color 1.3 --veil 0.7 --side right --text_w 0.5 --kicker 春はあけぼの --title 枕草子 --author 清少納言。版画の和紙は退色しているので、春らしく見せるには明るさ（dim 0.42 → 0.62）と色（--bg_color 1.3）を上げる
