#!/usr/bin/env python3
"""題名入りの静止画（1920×1080、文字のみ）を作る。動画の背景とサムネイルに使う。

使い方:
  python3 tools/make_thumbnail.py --title 雨ニモマケズ --author 宮沢賢治 \
      --series 朗読 --out narration/trial-01/out/thumbnail.png
縦書きの題名を右側に、作者名を左下に置く。フォントは tools/fonts/ipaexm.ttf（fetch_fonts.sh で取得）。
"""
import argparse, os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1920, 1080

# 回転が必要な記号（縦書きで横倒しにするもの）
ROTATE = set("ー〜（）「」『』【】―…‐-()[]")
# 縦書きで右上に寄せる小書き文字
SMALL = set("ぁぃぅぇぉっゃゅょゎァィゥェォッャュョヮ")


def load_font(size, bold=False):
    cands = [os.path.join(HERE, "fonts", "ipaexg.ttf" if bold else "ipaexm.ttf"),
             os.path.join(HERE, "fonts", "ipaexm.ttf"),
             "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
             "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"]
    for p in cands:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    sys.exit("日本語フォントが見つかりません。tools/fetch_fonts.sh を実行してください")


def draw_vertical(img, text, x_center, y_top, font, fill, spacing=1.08):
    """縦書き。x_center は文字列の中心 x。"""
    d = ImageDraw.Draw(img)
    size = font.size
    y = y_top
    for ch in text:
        if ch in ROTATE:
            tile = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0))
            td = ImageDraw.Draw(tile)
            td.text((size // 2, size // 2), ch, font=font, fill=fill)
            tile = tile.rotate(-90, resample=Image.BICUBIC)
            img.alpha_composite(tile, (int(x_center - size), int(y - size // 2)))
        else:
            bbox = d.textbbox((0, 0), ch, font=font)
            w = bbox[2] - bbox[0]
            dx = 0.12 * size if ch in SMALL else 0
            dy = -0.08 * size if ch in SMALL else 0
            d.text((x_center - w / 2 - bbox[0] + dx, y + dy), ch, font=font, fill=fill)
        y += size * spacing
    return y


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True)
    ap.add_argument("--author", default="")
    ap.add_argument("--series", default="")
    ap.add_argument("--note", default="", help="左下の小さな一行（例: 青空文庫より）")
    ap.add_argument("--out", required=True)
    ap.add_argument("--bg", default="#1b2430", help="背景色")
    ap.add_argument("--fg", default="#f3efe6", help="文字色")
    ap.add_argument("--accent", default="#c8a96a", help="差し色（罫線）")
    a = ap.parse_args()

    img = Image.new("RGBA", (W, H), a.bg)
    d = ImageDraw.Draw(img)

    # 右側に細い罫線を2本（縦書きの枠の気分）
    d.line([(W - 240, 90), (W - 240, H - 90)], fill=a.accent, width=3)
    d.line([(W - 1100, 90), (W - 1100, H - 90)], fill=a.accent, width=1)

    # 題名（縦書き、1行が収まるサイズに自動調整）
    n = max(len(a.title), 1)
    size = int(min(190, (H - 240) / (n * 1.08)))
    f_title = load_font(size)
    total = size * 1.08 * n
    y_top = (H - total) / 2 + 20
    draw_vertical(img, a.title, W - 470, y_top, f_title, a.fg)

    # 作者名（縦書き、題名の左、小さめ）
    if a.author:
        f_author = load_font(int(size * 0.42))
        draw_vertical(img, a.author, W - 740, y_top + size * 0.3, f_author, a.fg)

    # 左下：シリーズ名と注記（横書き）
    f_series = load_font(44)
    f_note = load_font(30)
    y = H - 150
    if a.series:
        d.text((120, y), a.series, font=f_series, fill=a.accent)
        y += 62
    if a.note:
        d.text((120, y), a.note, font=f_note, fill=a.fg)

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    img.convert("RGB").save(a.out, "PNG")
    print("wrote", a.out)


if __name__ == "__main__":
    main()
