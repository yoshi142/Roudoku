#!/usr/bin/env python3
"""サムネイル v2（1280×720 と 1920×1080）。docs/thumbnail-research.md の調査結果にもとづく。

方針（調査で伸びている朗読動画に共通していたこと）
- 作品名を画面でいちばん大きく、太い明朝体で、横幅の6〜8割を使って置く
- 背景は「人の手で作られたもの」に限る：本人が撮った写真、またはパブリックドメイン／CC0 の実写・版画
  （AI 生成画像は使わない。権利表記は backgrounds/README.md に書く）
- 背景を暗く（または明るく）均して、文字との明暗の差をはっきりさせる
- 作者名と朗読者名を必ず入れる（「誰が読むか」を見せる）
- スマートフォンの検索結果（幅 170px 前後）でも題名が読めることを確認する（--preview）

使い方:
  python3 tools/make_thumbnail_v2.py --bg tools/backgrounds/met_36521_shono.jpg --focus 0.5,0.5 \
      --title "雨ニモマケズ" --author 宮沢賢治 --narrator "朗読　〇〇" --theme dark \
      --out narration/trial-01/out/thumbnail_v2.png --preview
  題名の改行は「｜」。--theme light は明るい紙色の背景に黒文字（版画の余白を活かす）。
"""
import argparse, os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = {
    'black': os.path.join(HERE, 'fonts', 'ZenOldMincho-Black.ttf'),
    'bold': os.path.join(HERE, 'fonts', 'ShipporiMinchoB1-ExtraBold.ttf'),
    'regular': os.path.join(HERE, 'fonts', 'ipaexm.ttf'),
}


def font(kind, size):
    p = FONTS[kind]
    if not os.path.exists(p):
        sys.exit(f'フォントがありません: {p}（tools/fetch_fonts.sh を実行）')
    return ImageFont.truetype(p, size)


def cover(img, W, H, fx, fy, zoom=1.0):
    """画像を W×H に、焦点 (fx, fy) を中心に切り抜く。zoom>1 で拡大。"""
    iw, ih = img.size
    s = max(W / iw, H / ih) * zoom
    img = img.resize((int(iw * s + 0.5), int(ih * s + 0.5)), Image.LANCZOS)
    iw, ih = img.size
    x = min(max(int(fx * iw - W / 2), 0), iw - W)
    y = min(max(int(fy * ih - H / 2), 0), ih - H)
    return img.crop((x, y, x + W, y + H))


def fit_size(draw, lines, kind, max_w, max_h, start=400, spacing=1.12):
    size = start
    while size > 20:
        f = font(kind, size)
        ws = [draw.textlength(l, font=f) for l in lines]
        h = size * spacing * len(lines)
        if max(ws) <= max_w and h <= max_h:
            return f, size
        size -= 4
    return font(kind, 20), 20


def text_block(base, lines, f, x, y, fill, stroke_fill, stroke_w, shadow, spacing=1.12, align='left', box_w=None):
    W, H = base.size
    if shadow:
        sh = Image.new('RGBA', base.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(sh)
        yy = y
        for l in lines:
            lw = d.textlength(l, font=f)
            xx = x if align == 'left' else x + (box_w - lw) / 2
            d.text((xx + f.size * 0.03, yy + f.size * 0.04), l, font=f, fill=(0, 0, 0, 200))
            yy += f.size * spacing
        sh = sh.filter(ImageFilter.GaussianBlur(f.size * 0.06))
        base.alpha_composite(sh)
    d = ImageDraw.Draw(base)
    yy = y
    for l in lines:
        lw = d.textlength(l, font=f)
        xx = x if align == 'left' else x + (box_w - lw) / 2
        d.text((xx, yy), l, font=f, fill=fill, stroke_width=stroke_w, stroke_fill=stroke_fill)
        yy += f.size * spacing
    return yy


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bg', default=None, help='背景画像（なければ単色）')
    ap.add_argument('--focus', default='0.5,0.5', help='背景の切り抜きの中心（横,縦 0〜1）')
    ap.add_argument('--zoom', type=float, default=1.0, help='背景の拡大率')
    ap.add_argument('--veil', type=float, default=None, help='文字側の覆いの濃さ 0〜1（既定 dark 0.85 / light 0.92）')
    ap.add_argument('--title', required=True, help='「｜」で改行')
    ap.add_argument('--author', default='')
    ap.add_argument('--work', default='', help='題名とは別に作品名を添える（例: やまなし）')
    ap.add_argument('--narrator', default='', help='例: 朗読　〇〇')
    ap.add_argument('--kicker', default='', help='題名の上の小さな一行（例: 教科書で読んだ）')
    ap.add_argument('--theme', choices=['dark', 'light'], default='dark')
    ap.add_argument('--side', choices=['left', 'right'], default='left', help='文字を置く側')
    ap.add_argument('--text_w', type=float, default=0.62, help='題名に使う横幅の割合')
    ap.add_argument('--accent', default='#c8372d', help='差し色（朱色）')
    ap.add_argument('--thread', action='store_true', help='上から垂れる細い糸を1本描く（蜘蛛の糸用）')
    ap.add_argument('--bg_color', default=None)
    ap.add_argument('--out', required=True)
    ap.add_argument('--preview', action='store_true', help='スマートフォンの表示幅での見え方も書き出す')
    a = ap.parse_args()

    W, H = 1920, 1080
    dark = a.theme == 'dark'
    if a.bg:
        fx, fy = (float(v) for v in a.focus.split(','))
        img = cover(Image.open(a.bg).convert('RGB'), W, H, fx, fy, a.zoom)
        if dark:
            img = ImageEnhance.Brightness(img).enhance(0.62)
        img = img.convert('RGBA')
        # 文字側を暗く（明るく）するグラデーション
        g = Image.new('L', (W, 1))
        for x in range(W):
            t = x / W if a.side == 'right' else 1 - x / W
            g.putpixel((x, 0), int(255 * min(1, max(0, (t - 0.15) / 0.6)) ** 1.3))
        g = g.resize((W, H))
        veil = Image.new('RGBA', (W, H), (12, 14, 18, 255) if dark else (246, 241, 230, 255))
        k = a.veil if a.veil is not None else (0.85 if dark else 0.92)
        veil.putalpha(g.point(lambda v: int(v * k)))
        img.alpha_composite(veil)
    else:
        img = Image.new('RGBA', (W, H), a.bg_color or ('#111316' if dark else '#f4efe4'))

    d = ImageDraw.Draw(img)
    fg = (250, 248, 242, 255) if dark else (22, 20, 18, 255)
    stroke = (10, 10, 12, 255) if dark else (246, 241, 230, 255)
    margin = 110
    box_w = int(W * a.text_w)
    x0 = margin if a.side == 'left' else W - margin - box_w

    if a.thread:
        tx = x0 + box_w + 120 if a.side == 'left' else x0 - 120
        for i, alpha in enumerate([60, 120, 230]):
            d.line([(tx, 0), (tx, int(H * 0.78))], fill=(220, 225, 235, alpha), width=7 - i * 2)
        d.ellipse([tx - 5, int(H * 0.78) - 5, tx + 5, int(H * 0.78) + 5], fill=(230, 233, 240, 255))

    y = 120
    if a.kicker:
        fk = font('bold', 64)
        d.text((x0, y), a.kicker, font=fk, fill=a.accent if not dark else (240, 200, 120, 255))
        y += 100
    lines = a.title.split('｜')
    ft, size = fit_size(d, lines, 'black', box_w, H - y - 300)
    y_end = text_block(img, lines, ft, x0, y, fg, stroke, max(2, size // 28) if dark else 0, dark)

    sub = '　'.join(s for s in [a.author, f'『{a.work}』' if a.work else ''] if s)
    yb = H - 120
    if a.narrator:
        fn = font('bold', 66)
        d.text((x0, yb - 66), a.narrator, font=fn, fill=fg, stroke_width=2 if dark else 0, stroke_fill=stroke)
        yb -= 66 + 36
    if sub:
        fs = font('bold', 84)
        d.rectangle([x0, yb - 96, x0 + 14, yb - 4], fill=a.accent)
        d.text((x0 + 40, yb - 96), sub, font=fs, fill=fg, stroke_width=2 if dark else 0, stroke_fill=stroke)

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    out = img.convert('RGB')
    out.save(a.out, 'PNG')
    small = out.resize((1280, 720), Image.LANCZOS)
    small.save(os.path.splitext(a.out)[0] + '_1280.jpg', 'JPEG', quality=90)
    print('wrote', a.out, '題名の文字の大きさ', size, 'px')
    if a.preview:
        p = out.resize((246, 138), Image.LANCZOS)
        p.save(os.path.splitext(a.out)[0] + '_preview_small.png')


if __name__ == '__main__':
    main()
