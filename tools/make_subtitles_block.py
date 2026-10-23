#!/usr/bin/env python3
"""まとまり単位の字幕（既定は縦書き）。台本の連（空行で区切られた行のまとまり）ごとに、画面の中央に出す。

本人の指示（2026-10-23）：「朗読の字幕は短くないほうがよい。文章の塊で字幕をつける」「縦書きの方がいいかも」。
- まとまりは “連”。連が長いとき（既定 5行以上）は、4行以下に均等に分ける（雨ニモマケズの「東に…」〜「やめろと言い」の8行は4行ずつ）
- 連の最初の行を読み始める少し前にフェードインし、最後の行を読み終えて少し残してからフェードアウトする
- 縦書き：右から左へ行を並べ、行の頭をそろえる。句読点は字の右上、小さい「っ」「ゃ」などは少し右上に寄せ、
  「ー」や括弧は90度回す。字幕の仕組み（ASS）の縦書きはこれらが崩れやすいので、字幕を1枚ずつ画像（PNG）で作る
- 文字は台本から取る（「## 字幕の書き換え」の欄も使う）。書体はしっぽり明朝 Medium、生成りの白、柔らかい影

使い方:
  python3 tools/make_subtitles_block.py narration/trial-01/out/auto2/timeline.json narration/trial-01/script.md \\
      --out narration/trial-01/out/subs_block [--horizontal] [--max_lines 4]
出力: <out>/block_NN.png（1920×1080、透明）、<out>/overlays.json（画像と表示の時刻。make_reading_video.py --overlays に渡す）、
      <out>.srt（YouTube の字幕ファイル用。まとまりごと）
"""
import argparse, json, math, os, re, sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auto_edit import kana, script_text  # noqa: E402
from make_subtitles import script_display, ts_srt  # noqa: E402

W, H = 1920, 1080
FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
SMALL = set("ぁぃぅぇぉっゃゅょゎァィゥェォッャュョヮヵヶ")
PUNCT = set("、。，．")
ROTATE = set("ー－―…‥〜～（）()「」『』【】［］〔〕：；")


def overrides_of(path):
    st = open(path, encoding="utf-8").read()
    ov = {}
    mo = re.search(r"^##\s*字幕の書き換え.*?\n(.*?)(?=^##\s|\Z)", st, re.S | re.M)
    if mo:
        for line in mo.group(1).splitlines():
            m2 = re.match(r"^\s*[-・]?\s*(.+?)\s*(?:→|->)\s*(.+?)\s*$", line)
            if m2:
                ov[m2.group(1)] = m2.group(2)
    return ov


def line_events(tl, rlines, dlines):
    """句ごとに台本の行を決め、行ごとの読みの開始・終了（完成音声の秒）を返す（make_subtitles.py と同じ考え方）。"""
    starts, pos = [], 0
    for r in rlines:
        starts.append(pos)
        pos += len(kana(r))

    def line_of(x):
        i = 0
        for j, s in enumerate(starts):
            if s <= x and dlines[j].strip():
                i = j
        return i
    li_of = [line_of((p["script"][0] + p["script"][1] - 1) / 2) if p["script"] else None for p in tl]
    for i, p in enumerate(tl):
        if li_of[i] is not None:
            continue
        prev = next(((tl[j]["out_e"], li_of[j]) for j in range(i - 1, -1, -1) if li_of[j] is not None), None)
        nxt = next(((tl[j]["out_s"], li_of[j]) for j in range(i + 1, len(tl)) if li_of[j] is not None), None)
        c = []
        if prev:
            c.append((p["out_s"] - prev[0], prev[1]))
        if nxt:
            c.append((nxt[0] - p["out_e"], nxt[1]))
        if c:
            li_of[i] = min(c)[1]
    ev = {}
    for p, li in zip(tl, li_of):
        if li is None:
            continue
        s, e = ev.get(li, (p["out_s"], p["out_e"]))
        ev[li] = (min(s, p["out_s"]), max(e, p["out_e"]))
    return ev


def stanzas(dlines, skip_first):
    groups, cur = [], []
    for i, l in enumerate(dlines):
        if i == 0 and skip_first:
            continue
        if l.strip():
            cur.append(i)
        elif cur:
            groups.append(cur); cur = []
    if cur:
        groups.append(cur)
    return groups


def split_even(g, max_lines):
    if len(g) <= max_lines:
        return [g]
    k = math.ceil(len(g) / max_lines)
    size = math.ceil(len(g) / k)
    return [g[i:i + size] for i in range(0, len(g), size)]


def draw_vertical(lines, font, size, out):
    pitch_y = int(size * 1.06)      # 字の送り
    pitch_x = int(size * 1.95)      # 行の送り
    max_chars = max(1, (H - 130) // pitch_y)
    cols = []
    for l in lines:                 # 長い行だけ折り返す（52px で17字まで1行）
        for k in range(0, len(l), max_chars):
            cols.append(l[k:k + max_chars])
    height = max(len(c) for c in cols) * pitch_y
    width = (len(cols) - 1) * pitch_x + size
    x_right = W // 2 + width // 2 - size // 2   # 一番右の行の中心
    y0 = (H - height) // 2
    txt = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(txt)
    fill = (238, 232, 220, 235)
    for ci, col in enumerate(cols):
        cx = x_right - ci * pitch_x
        for k, ch in enumerate(col):
            cy = y0 + k * pitch_y + pitch_y // 2   # マスの中心
            if ch in " 　":
                continue
            if ch in ROTATE:
                cell = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0))
                ImageDraw.Draw(cell).text((size, size), ch, font=font, fill=fill, anchor="mm")
                cell = cell.rotate(-90, resample=Image.BICUBIC)
                txt.alpha_composite(cell, (cx - size, cy - size))
            elif ch in PUNCT:
                d.text((cx + int(size * 0.32), cy - int(size * 0.30)), ch, font=font, fill=fill, anchor="mm")
            elif ch in SMALL:
                d.text((cx + int(size * 0.07), cy - int(size * 0.07)), ch, font=font, fill=fill, anchor="mm")
            else:
                d.text((cx, cy), ch, font=font, fill=fill, anchor="mm")
    finish(txt, out)


def draw_horizontal(lines, font, size, out):
    pitch = int(size * 1.7)
    txt = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(txt)
    y0 = (H - pitch * len(lines)) // 2
    for i, l in enumerate(lines):
        w = d.textlength(l, font=font)
        d.text(((W - w) / 2, y0 + i * pitch), l, font=font, fill=(238, 232, 220, 235))
    finish(txt, out)


def finish(txt, out):
    # 柔らかい影（文字の形をぼかした暗い縁）を下に敷く。くっきりさせすぎない
    a = txt.split()[3]
    shadow = Image.new("RGBA", (W, H), (12, 10, 8, 0))
    shadow.putalpha(a.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(6)).point(lambda v: int(v * 0.75)))
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    img.alpha_composite(shadow)
    img.alpha_composite(txt.filter(ImageFilter.GaussianBlur(0.6)))
    img.save(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("timeline"); ap.add_argument("script")
    ap.add_argument("--out", required=True)
    ap.add_argument("--horizontal", action="store_true", help="横書きにする（既定は縦書き）")
    ap.add_argument("--max_lines", type=int, default=4, help="1画面の行数の上限（これより長い連は均等に分ける）")
    ap.add_argument("--size", type=int, default=52)
    ap.add_argument("--lead", type=float, default=0.4, help="読み始めの何秒前から出すか")
    ap.add_argument("--hold", type=float, default=1.0, help="まとまりを読み終えてから何秒残すか（次の手前まで）")
    ap.add_argument("--last_hold", type=float, default=3.5)
    ap.add_argument("--fade_in", type=float, default=0.8)
    ap.add_argument("--fade_out", type=float, default=0.7)
    a = ap.parse_args()

    tl = json.load(open(a.timeline, encoding="utf-8"))["phrases"]
    rlines = script_text(a.script).split("\n")
    dlines = script_display(a.script).split("\n")
    if len(rlines) != len(dlines):
        sys.exit("台本の行の数が合いません")
    ov = overrides_of(a.script)
    ev = line_events(tl, rlines, dlines)
    head = bool(re.search(r"^#\s*台本：", open(a.script, encoding="utf-8").read(), re.M))
    chunks = []
    for g in stanzas(dlines, head):
        for c in split_even(g, a.max_lines):
            read = [ev[i] for i in c if i in ev]
            if not read:
                continue
            chunks.append(([ov.get(dlines[i].strip(), dlines[i].strip()) for i in c],
                           min(s for s, _ in read), max(e for _, e in read)))
    os.makedirs(a.out, exist_ok=True)
    font = ImageFont.truetype(os.path.join(FONTS, "ShipporiMincho-Medium.ttf"), a.size)
    items = []
    for k, (lines, s, e) in enumerate(chunks):
        nxt = chunks[k + 1][1] if k + 1 < len(chunks) else None
        start = max(0.0, s - a.lead)
        end = e + (a.last_hold if nxt is None else a.hold)
        if nxt is not None:
            end = min(end, nxt - a.lead - 0.1)
        if items and start < items[-1]["end"] + 0.05:
            start = items[-1]["end"] + 0.05
        png = os.path.join(a.out, f"block_{k + 1:02d}.png")
        (draw_horizontal if a.horizontal else draw_vertical)(lines, font, a.size, png)
        items.append({"png": png, "start": round(start, 3), "end": round(max(end, start + 1.0), 3),
                      "fade_in": a.fade_in, "fade_out": a.fade_out, "lines": lines})
    json.dump(items, open(os.path.join(a.out, "overlays.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(a.out + ".srt", "w", encoding="utf-8") as f:
        for i, it in enumerate(items, 1):
            f.write(f"{i}\n{ts_srt(it['start'])} --> {ts_srt(it['end'])}\n" + "\n".join(it["lines"]) + "\n\n")
    print(f"字幕 {len(items)} まとまり（{'横書き' if a.horizontal else '縦書き'}）→ {a.out}/overlays.json、{a.out}.srt")
    for it in items:
        print(f"  {it['start']:6.2f}-{it['end']:6.2f}  " + "／".join(it["lines"]))


if __name__ == "__main__":
    main()
