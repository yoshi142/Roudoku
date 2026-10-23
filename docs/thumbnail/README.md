# サムネイル試作（v2）

調査（docs/thumbnail-research.md）にもとづく試作。1280×720。`_small.png` は幅246ピクセルに縮めたときの見え方。
朗読者名は「〇〇〇〇」のまま（本人の名前か通称が決まったら差し替える）。

作り方（例）：
```
python3 tools/make_thumbnail_v2.py --bg tools/backgrounds/met_36521_hiroshige_shono_hakuu.jpg --focus 0.62,0.5 \
  --side left --text_w 0.8 --title "雨ニモマケズ" --author 宮沢賢治 --narrator "朗読　〇〇〇〇" \
  --out narration/trial-01/out/thumbnail_v2.png --preview

python3 tools/make_thumbnail_v2.py --bg tools/backgrounds/met_54091_hokusai_crab.jpg --zoom 1.9 --focus 0.40,0.50 \
  --theme light --side right --text_w 0.52 --veil 0.95 --title "クラムボンは｜かぷかぷ｜笑ったよ" \
  --author 宮沢賢治 --work やまなし --narrator "朗読　〇〇〇〇" \
  --out narration/trial-02-yamanashi/out/thumbnail_v2.png --preview

python3 tools/make_thumbnail_v2.py --side left --thread --text_w 0.66 --title "蜘蛛の糸" --author 芥川龍之介 \
  --narrator "朗読　〇〇〇〇" --out narration/trial-05-kumonoito/out/thumbnail_v2.png --preview
```
背景の出典は tools/backgrounds/README.md。
