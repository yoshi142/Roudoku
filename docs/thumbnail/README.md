# サムネイル試作（v2）

調査（docs/thumbnail-research.md）にもとづく試作。1280×720。`_small.png` は幅246ピクセルに縮めたときの見え方。
朗読者名は出さない（本人の決定、2026-10-23）。--narrator は使わない。下の3点は 2026-10-23 に名前の行を外して作り直した（設定値は元の画像との画素の差が最も小さいものを選んだ）。

作り方（例）：
```
python3 tools/make_thumbnail_v2.py --bg tools/backgrounds/met_36521_hiroshige_shono_hakuu.jpg --focus 0.62,0.5 \
  --side left --text_w 0.8 --title "雨ニモマケズ" --author 宮沢賢治 --bg_bright 0.9 --veil 0.6 --bg_color 1.3 \
  --out narration/trial-01/out/thumbnail_v2.png --preview

python3 tools/make_thumbnail_v2.py --bg tools/backgrounds/met_54091_hokusai_crab.jpg --zoom 1.9 --focus 0.40,0.50 \
  --theme light --side right --text_w 0.52 --veil 0.95 --title "クラムボンは｜かぷかぷ｜笑ったよ" \
  --author 宮沢賢治 --work やまなし --veil 0.85 --bg_bright 0.62 \
  --out narration/trial-02-yamanashi/out/thumbnail_v2.png --preview

python3 tools/make_thumbnail_v2.py --side left --thread --text_w 0.66 --title "蜘蛛の糸" --author 芥川龍之介 \
  --fill "#3a4f73" --out narration/trial-05-kumonoito/out/thumbnail_v2.png --preview
```
背景の出典は tools/backgrounds/README.md。
