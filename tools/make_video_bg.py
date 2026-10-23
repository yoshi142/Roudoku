#!/usr/bin/env python3
"""字幕を画面中央に出す動画のための背景（1920×1080）。

サムネイルは中央に大きな題名があるので、そのままでは字幕と重なる。動画には別の背景を使う。
- 背景画像を暗めにし（--dim）、ごく軽くぼかして（--blur）、中央の字幕が読みやすいようにする
- 中央を少しだけ暗くする（字幕の下地。輪郭の見えない柔らかい楕円）
- 題名と作者名は左上に小さく。差し色は朱 #c8372d の短い縦線（サムネイルと共通）
- 背景はサムネイルと同じく、本人の写真か PD／CC0 の画像に限る（tools/backgrounds/README.md）

使い方:
  python3 tools/make_video_bg.py --bg tools/backgrounds/met_36521_hiroshige_shono_hakuu.jpg --focus 0.62,0.5 \\
      --title 雨ニモマケズ --author 宮沢賢治 --out narration/trial-01/out/video_bg.png
"""
import argparse, os
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

W, H = 1920, 1080
FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")


def cover(img, focus, zoom):
    fx, fy = focus
    iw, ih = img.size
    s = max(W / iw, H / ih) * zoom
    img = img.resize((int(iw * s), int(ih * s)), Image.LANCZOS)
    iw, ih = img.size
    x = min(max(0, int(fx * iw - W / 2)), iw - W)
    y = min(max(0, int(fy * ih - H / 2)), ih - H)
    return img.crop((x, y, x + W, y + H))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bg"); ap.add_argument("--fill", default="#20242b")
    ap.add_argument("--focus", default="0.5,0.5"); ap.add_argument("--zoom", type=float, default=1.0)
    ap.add_argument("--dim", type=float, default=0.42, help="背景の明るさ（1で元のまま）")
    ap.add_argument("--color", type=float, default=0.85, help="背景の色の濃さ（1で元のまま）")
    ap.add_argument("--blur", type=float, default=1.6)
    ap.add_argument("--center_shade", type=float, default=0.35, help="中央の下地の濃さ 0〜1")
    ap.add_argument("--title", required=True); ap.add_argument("--author", default="")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    if a.bg:
        img = cover(Image.open(a.bg).convert("RGB"), tuple(map(float, a.focus.split(","))), a.zoom)
        img = ImageEnhance.Color(img).enhance(a.color)
        img = ImageEnhance.Brightness(img).enhance(a.dim)
        img = img.filter(ImageFilter.GaussianBlur(a.blur))
    else:
        img = Image.new("RGB", (W, H), a.fill)
    img = img.convert("RGBA")

    # 中央の柔らかい下地
    shade = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(shade)
    d.ellipse((W * 0.12, H * 0.30, W * 0.88, H * 0.70), fill=int(255 * a.center_shade))
    shade = shade.filter(ImageFilter.GaussianBlur(120))
    black = Image.new("RGBA", (W, H), (8, 8, 10, 255))
    black.putalpha(shade)
    img.alpha_composite(black)

    # 左上の題名と作者名。背景の文字（版画の題字など）と重ならないよう、左上だけ柔らかく暗くする
    corner = Image.new("L", (W, H), 0)
    ImageDraw.Draw(corner).ellipse((-420, -300, 820, 420), fill=150)
    corner = corner.filter(ImageFilter.GaussianBlur(90))
    dark = Image.new("RGBA", (W, H), (8, 8, 10, 255))
    dark.putalpha(corner)
    img.alpha_composite(dark)
    d = ImageDraw.Draw(img)
    ft = ImageFont.truetype(os.path.join(FONTS, "ShipporiMincho-Medium.ttf"), 46)
    fa = ImageFont.truetype(os.path.join(FONTS, "ShipporiMincho-Regular.ttf"), 30)
    x, y = 96, 84
    d.rectangle((x, y + 6, x + 5, y + 50), fill=(200, 55, 45, 235))
    d.text((x + 24, y), a.title, font=ft, fill=(238, 232, 220, 225))
    if a.author:
        d.text((x + 26, y + 66), a.author, font=fa, fill=(238, 232, 220, 190))
    img.convert("RGB").save(a.out)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
