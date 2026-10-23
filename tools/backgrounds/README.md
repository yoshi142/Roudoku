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

取得日：2026-10-23（原 朝之富士は Part 3 で追加。枕草子の動画に使用。左上の版画の題字と画面の題名が重ならないよう、make_video_bg.py --zoom 1.45 --focus 0.98,0.36 で右寄りに切り抜いた）。メトロポリタン美術館の Open Access 画像は CC0（著作権を放棄、商用利用可、表記は任意）。説明文に「背景：歌川広重『庄野 白雨』（メトロポリタン美術館所蔵、パブリックドメイン）」のように書くと、出どころが分かり信頼につながる。

探し方：Met の検索 API（https://collectionapi.metmuseum.org/public/collection/v1.1/search?q=語&hasImages=true&isPublicDomain=true）。旧 /v1/search は 2026-10-01 に廃止。
Wikimedia Commons の API はこの環境から回数制限にかかりやすい。
