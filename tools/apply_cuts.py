#!/usr/bin/env python3
"""cuts.txt に書かれた区間を取り除いた音声を作る（言い直しの切り詰め）。

cuts.txt の書式（1行1区間、秒。# 以降はコメント）:
  12.40 18.95   # 「丈夫な体を持ち」言い直し。手をたたく音を含む
  95.10 97.00
使い方: python3 tools/apply_cuts.py input.wav cuts.txt output.wav [--xfade 0.03]
つなぎ目は短いクロスフェード（既定 30ms）で、クリック音を避ける。
"""
import argparse, subprocess, sys


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", path], capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input"); ap.add_argument("cuts"); ap.add_argument("output")
    ap.add_argument("--xfade", type=float, default=0.03)
    a = ap.parse_args()
    cuts = []
    for line in open(a.cuts, encoding="utf-8"):
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        s, e = map(float, line.split()[:2])
        if e <= s:
            sys.exit(f"不正な区間: {line}")
        cuts.append((s, e))
    cuts.sort()
    total = duration(a.input)
    keep, pos = [], 0.0
    for s, e in cuts:
        if s > pos:
            keep.append((pos, s))
        pos = max(pos, e)
    if pos < total:
        keep.append((pos, total))
    if not cuts:
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", a.input, a.output], check=True)
        print("切り詰めなし。コピーしました"); return
    parts = []
    for i, (s, e) in enumerate(keep):
        parts.append(f"[0:a]atrim=start={s:.3f}:end={e:.3f},asetpts=PTS-STARTPTS[k{i}]")
    chain = "[k0]"
    for i in range(1, len(keep)):
        parts.append(f"{chain}[k{i}]acrossfade=d={a.xfade}:c1=tri:c2=tri[x{i}]")
        chain = f"[x{i}]"
    fc = ";".join(parts)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", a.input, "-filter_complex", fc,
                    "-map", chain, a.output], check=True)
    removed = sum(e - s for s, e in cuts)
    print(f"区間 {len(cuts)} か所、合計 {removed:.1f} 秒を取り除きました → {a.output}（{duration(a.output):.1f} 秒）")


if __name__ == "__main__":
    main()
