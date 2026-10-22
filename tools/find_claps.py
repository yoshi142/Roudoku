#!/usr/bin/env python3
"""言い直しの合図（手を1回たたく音）の候補を探す。

録音の手引きでは「2秒黙る → 手を1回たたく → 1秒黙る → 行の頭から読み直す」としている。
この条件（直前に静けさがあり、極めて短く鋭い音）に合う位置を列挙する。最終判断は人が波形と音で確認する。
使い方: python3 tools/find_claps.py input.wav [--threshold_db -12] [--pre_quiet_sec 1.0]
出力: 秒単位の候補と、その前後の静けさ。cuts.txt の下書きとしても使える。
"""
import argparse, subprocess, sys
import numpy as np


def load_mono(path, sr=16000):
    cmd = ["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32), sr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--threshold_db", type=float, default=-12.0, help="ピークがこの値(dBFS)以上")
    ap.add_argument("--pre_quiet_sec", type=float, default=1.0, help="直前にこの秒数以上の静けさ")
    ap.add_argument("--quiet_db", type=float, default=-45.0, help="静けさの基準(dBFS, RMS)")
    a = ap.parse_args()
    x, sr = load_mono(a.path)
    hop = int(sr * 0.02)  # 20ms
    n = len(x) // hop
    frames = x[: n * hop].reshape(n, hop)
    peak_db = 20 * np.log10(np.max(np.abs(frames), axis=1) + 1e-9)
    rms_db = 20 * np.log10(np.sqrt(np.mean(frames ** 2, axis=1)) + 1e-9)
    pre = int(a.pre_quiet_sec / 0.02)
    out = []
    i = pre
    while i < n:
        if peak_db[i] >= a.threshold_db:
            before = rms_db[i - pre:i]
            # 直前が静か、かつ音が短い（0.3秒以内に静けさへ戻る）
            j = i
            while j < n and rms_db[j] > a.quiet_db + 10 and j - i < 25:
                j += 1
            short = (j - i) <= 15
            if np.mean(before < a.quiet_db) > 0.8 and short:
                out.append((i * 0.02, (j - i) * 0.02, float(peak_db[i])))
                i = j + 25
                continue
        i += 1
    if not out:
        print("候補なし（threshold_db や pre_quiet_sec を緩めて再実行）")
        return
    print("# 時刻(秒)  長さ(秒)  ピーク(dBFS)   ← 言い直しの合図の候補")
    for t, L, p in out:
        m, s = divmod(t, 60)
        print(f"{t:8.2f}  {L:5.2f}  {p:7.1f}   ({int(m)}:{s:05.2f})")


if __name__ == "__main__":
    main()
