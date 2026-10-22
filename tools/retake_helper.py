#!/usr/bin/env python3
"""手拍子（言い直しの合図）の前後の文字起こしを並べ、cuts.txt の下書きを作る。

手順: find_claps.py で合図の候補を出し、transcribe.py で文字起こしを作ったあと、
  python3 tools/retake_helper.py transcript.tsv claps.txt > cuts_draft.txt
claps.txt は find_claps.py の出力をそのまま保存したもの（先頭の数値列を時刻として読む）。
各合図について、直前の数行と直後の数行を表示し、「合図の直後に読み直された文」と
最もよく似た「合図の前の文」の開始時刻を切り詰めの開始候補にする。最終判断は人が行う。
"""
import sys, difflib


def main():
    tsv, claps = sys.argv[1], sys.argv[2]
    segs = []
    for line in open(tsv, encoding="utf-8").read().splitlines()[1:]:
        s, e, t = line.split("\t", 2)
        segs.append((float(s), float(e), t))
    times = []
    for line in open(claps, encoding="utf-8"):
        p = line.split()
        if p and p[0][0].isdigit():
            times.append(float(p[0]))
    for ct in times:
        before = [x for x in segs if x[1] <= ct + 0.2][-4:]
        after = [x for x in segs if x[0] >= ct - 0.2][:2]
        if not after:
            print(f"# {ct:.2f}s: 合図のあとに発話が見つからない（録音の末尾か）"); continue
        target = after[0][2]
        best, score = None, 0.0
        for x in before:
            r = difflib.SequenceMatcher(None, x[2], target).ratio()
            if r > score:
                best, score = x, r
        start = best[0] if best and score >= 0.4 else (before[-1][0] if before else ct - 3)
        end = after[0][0] - 0.15
        print(f"{start:.2f} {end:.2f}  # 合図 {ct:.2f}s  類似度 {score:.2f}")
        for x in before:
            print(f"#    前 [{x[0]:7.2f}] {x[2]}")
        for x in after:
            print(f"#    後 [{x[0]:7.2f}] {x[2]}")
        print()


if __name__ == "__main__":
    main()
