#!/usr/bin/env python3
"""台本と自動編集の記録（timeline.json）から字幕を作る（ASS と SRT）。

字幕の文字は台本から取る（漢字かな交じりの正しい表記）。表示する時刻は、録音のどの句が台本のどの行に
当たるか（tools/auto_edit.py の timeline.json）で決める。1行の字幕は、その行を読んでいるあいだ表示する。

見た目（本人の指示、2026-10-23）：画面の中央。くっきりさせすぎず、落ち着いた見た目。
パッと切り替えず、フェードイン・フェードアウトする。
- 書体：しっぽり明朝 Medium（tools/fonts/。SIL OFL）
- 色：生成りの白（#EEE8DC）を少し透かす。縁取りは細く暗く、ぼかして柔らかい影にする
- フェード：入り 0.6秒、出 0.5秒

使い方:
  python3 tools/make_subtitles.py narration/trial-01/out/auto/timeline.json narration/trial-01/script.md \\
      --out narration/trial-01/out/subtitles
出力: <out>.ass（動画に焼き込む用）、<out>.srt（YouTube に字幕ファイルとして上げる用）

--gloss に「| 原文 | 現代語訳 |」の表を含む md（古典の台本の「字幕用の対訳」）を渡すと、原文の下に現代語訳を
小さく、少し薄く出す（本人の指示、2026-10-23：古典の現代語訳は読まず、字幕で原文と並べて出す）。
"""
import argparse, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auto_edit import kana, script_text  # noqa: E402


def script_display(path):
    """台本の朗読部分を、表示用の文字（読みがなを外し、漢字を残す）で行ごとに返す。行の並びは script_text と同じ。"""
    t = open(path, encoding="utf-8").read()
    head = ""
    h = re.search(r"^#\s*台本：\s*(.+?)「(.+?)」", t, re.M)
    if h:
        head = h.group(2) + "　" + h.group(1) + "\n"
    body = t
    m = re.search(r"##\s*\d*\s*　?朗読.*?\n(.*?)(?=\n##\s|\n---)", t, re.S)
    if m:
        body = m.group(1)
    body = re.sub(r"【[^】]*】", "", body)
    body = re.sub(r"（[^）]*）", "", body)
    body = re.sub(r"^#.*$", "", body, flags=re.M)
    return head + body.replace("／", "")


def norm(t):
    return re.sub(r"[\s、。，．,.「」『』]", "", t)


def load_gloss(path):
    """md の表「| 原文 | 現代語訳 |」から {原文（句読点なし）: 訳} を作る。"""
    g = {}
    for line in open(path, encoding="utf-8"):
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) == 2 and c[0] not in ("原文", "") and not set(c[0]) <= set("-: "):
            g[norm(c[0])] = c[1]
    return g


def ts_ass(t):
    t = max(0.0, t)
    h, r = divmod(t, 3600); m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def ts_srt(t):
    t = max(0.0, t)
    h, r = divmod(t, 3600); m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}".replace(".", ",")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("timeline"); ap.add_argument("script")
    ap.add_argument("--out", required=True)
    ap.add_argument("--size", type=int, default=68, help="文字の大きさ（1080p での px）")
    ap.add_argument("--fade_in", type=float, default=0.6)
    ap.add_argument("--fade_out", type=float, default=0.5)
    ap.add_argument("--lead", type=float, default=0.25, help="読み始めの何秒前から出すか")
    ap.add_argument("--gloss", help="対訳の表を含む md。原文の下に現代語訳を出す")
    ap.add_argument("--gloss_size", type=int, default=44, help="現代語訳の文字の大きさ（px）")
    ap.add_argument("--hold", type=float, default=1.2, help="読み終わってから何秒残すか（次の行の手前まで）")
    ap.add_argument("--last_hold", type=float, default=3.5, help="最後の行を読み終わってから何秒残すか（余韻）")
    a = ap.parse_args()

    tl = json.load(open(a.timeline, encoding="utf-8"))["phrases"]
    # 台本の「## 字幕の書き換え」の欄（「元の行 → 字幕に出す文字」）。読みは変えずに、字幕だけを変える
    # 例：ひどりのときは涙を流し → ひどり（ひでり）のときは涙を流し（本人の指示、2026-10-23）
    overrides = {}
    st = open(a.script, encoding="utf-8").read()
    mo = re.search(r"^##\s*字幕の書き換え.*?\n(.*?)(?=^##\s|\Z)", st, re.S | re.M)
    if mo:
        for line in mo.group(1).splitlines():
            m2 = re.match(r"^\s*[-・]?\s*(.+?)\s*(?:→|->)\s*(.+?)\s*$", line)
            if m2:
                overrides[m2.group(1)] = m2.group(2)
    rlines = script_text(a.script).split("\n")
    dlines = script_display(a.script).split("\n")
    if len(rlines) != len(dlines):
        sys.exit(f"台本の行の数が合いません（{len(rlines)} と {len(dlines)}）")
    # 行ごとの台本の仮名の位置
    starts, pos = [], 0
    for r in rlines:
        starts.append(pos)
        pos += len(kana(r))
    def line_of(x):
        i = 0
        for j, st in enumerate(starts):
            if st <= x and dlines[j].strip():
                i = j
        return i

    # 句ごとに行を決める。台本に当たらない句（本人が足した語や、切れた短い句）は、時間の近いほうの句の行に入れる
    li_of = [line_of((p["script"][0] + p["script"][1] - 1) / 2) if p["script"] else None for p in tl]
    for i, p in enumerate(tl):
        if li_of[i] is not None:
            continue
        prev = next(((tl[j]["out_e"], li_of[j]) for j in range(i - 1, -1, -1) if li_of[j] is not None), None)
        nxt = next(((tl[j]["out_s"], li_of[j]) for j in range(i + 1, len(tl)) if li_of[j] is not None), None)
        cands = []
        if prev:
            cands.append((p["out_s"] - prev[0], prev[1]))
        if nxt:
            cands.append((nxt[0] - p["out_e"], nxt[1]))
        if cands:
            li_of[i] = min(cands)[1]
    events = []  # [行番号, 開始, 終了]
    for p, li in zip(tl, li_of):
        if li is None:
            continue
        if events and events[-1][0] == li:
            events[-1][2] = p["out_e"]
        else:
            events.append([li, p["out_s"], p["out_e"]])
    # 題名の行と作者の行は1つにまとめて出す（見出しは script_display で1行）
    out = []
    for k, (li, s, e) in enumerate(events):
        nxt = events[k + 1][1] if k + 1 < len(events) else e + 3
        start = s - a.lead
        end = min(e + (a.last_hold if k + 1 == len(events) else a.hold), nxt - a.lead - 0.05)
        if out and start < out[-1][2] + 0.02:
            start = out[-1][2] + 0.02
        text = dlines[li].strip()
        out.append((overrides.get(text, text), start, max(end, start + 0.8)))

    font = "Shippori Mincho Medium"
    ass = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Reading,{font},{a.size},&H18DCE8EE,&H18DCE8EE,&H80141210,&HA0000000,0,0,0,0,100,100,4,0,1,1.6,0,5,160,160,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    fi, fo = int(a.fade_in * 1000), int(a.fade_out * 1000)
    gloss = load_gloss(a.gloss) if a.gloss else {}
    if gloss:
        miss = [t for t, _, _ in out if norm(t) not in gloss]
        if miss:
            print("対訳の表にない行（訳なしで出す）:", miss)
    sub = lambda t: gloss.get(norm(t), "")
    for text, s, e in out:
        g = sub(text)
        # 原文の下に小さな空き行をはさみ、訳を小さく少し薄く出す
        g = f"\\N{{\\fs{a.gloss_size // 2}}}\\N{{\\fs{a.gloss_size}\\alpha&H40&}}{g}" if g else ""
        ass += f"Dialogue: 0,{ts_ass(s)},{ts_ass(e)},Reading,,0,0,0,,{{\\fad({fi},{fo})\\blur2.5}}{text}{g}\n"
    open(a.out + ".ass", "w", encoding="utf-8").write(ass)
    with open(a.out + ".srt", "w", encoding="utf-8") as f:
        for i, (text, s, e) in enumerate(out, 1):
            g = sub(text)
            f.write(f"{i}\n{ts_srt(s)} --> {ts_srt(e)}\n{text}" + (f"\n{g}" if g else "") + "\n\n")
    print(f"字幕 {len(out)} 行 → {a.out}.ass / {a.out}.srt")
    for text, s, e in out:
        print(f"  {s:6.2f}-{e:6.2f}  {text}")


if __name__ == "__main__":
    main()
