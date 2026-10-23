#!/usr/bin/env python3
"""声に軽いリバーブ（残響）をかける。整音（tools/process_audio.sh）の前に使う。

ffmpeg の aecho は “やまびこ” のような不自然な響きになりやすいので使わない。部屋の響き（インパルス応答）を
数式で作り、声に畳み込んで、元の声と混ぜる。
- 響きは、少しの間（プリディレイ）のあと、数本の初期反射と、指数的に減っていく拡散音（ノイズ）で作る
- 高い音ほど早く減衰させる（実際の部屋に近い。高域が残ると金属的に聞こえる）
- 響きの帯域は 200Hz〜7kHz に絞る（低音がこもらず、HE-AAC 録音の高域のザラつきを広げない）

使い方:
  python3 tools/add_reverb.py in.wav out.wav [--rt 1.2] [--wet 0.16] [--predelay 0.025]
  --rt     残響時間（秒。音が 60 dB 下がるまで）。小さな部屋 0.6〜0.9、広い部屋 1.0〜1.5、ホール 1.8〜
  --wet    響きの割合（0〜1）。0.10〜0.18 くらいが「少し」
依存: numpy、ffmpeg（すべて無料）
"""
import argparse, subprocess
import numpy as np

SR = 48000


def load(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


def onepole_lp(x, fc):
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc = (1 - a) * v + a * acc
        y[i] = acc
    return y


def band(x, lo=200.0, hi=7000.0):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    g = 1 / np.sqrt(1 + (lo / np.maximum(f, 1)) ** 4) / np.sqrt(1 + (f / hi) ** 4)
    return np.fft.irfft(X * g, len(x))


def impulse(rt, predelay, seed=7):
    rng = np.random.default_rng(seed)
    n = int(SR * min(rt * 1.4, 4.0))
    t = np.arange(n) / SR
    # 拡散音：低い帯域と高い帯域で減衰の速さを変える（高域は約 0.55 倍の残響時間）
    noise = rng.standard_normal(n)
    low = onepole_lp(noise, 2500.0)
    high = noise - low
    tail = low * np.exp(-6.91 * t / rt) + high * np.exp(-6.91 * t / (rt * 0.55))
    # 立ち上がりを柔らかく（拡散音は 15ms かけて増える）
    tail *= np.minimum(1.0, t / 0.015)
    ir = np.zeros(n + int(SR * predelay))
    ir[int(SR * predelay):] = tail
    # 初期反射（数本）
    for d, g in [(0.011, 0.5), (0.017, 0.35), (0.023, 0.3), (0.031, 0.22), (0.041, 0.15)]:
        k = int(SR * (predelay * 0.5 + d))
        if k < len(ir):
            ir[k] += g * 8 * np.std(tail[: SR // 50])
    ir = band(ir)
    return ir / np.sqrt(np.sum(ir ** 2))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input"); ap.add_argument("output")
    ap.add_argument("--rt", type=float, default=1.2)
    ap.add_argument("--wet", type=float, default=0.16)
    ap.add_argument("--predelay", type=float, default=0.025)
    a = ap.parse_args()
    x = load(a.input)
    ir = impulse(a.rt, a.predelay)
    n = len(x) + len(ir) - 1
    N = 1 << (n - 1).bit_length()
    wet = np.fft.irfft(np.fft.rfft(x, N) * np.fft.rfft(ir, N), N)[: len(x)]
    # 響きの大きさを元の声の大きさにそろえてから、割合で混ぜる
    wet *= np.sqrt(np.mean(x ** 2) / max(np.mean(wet ** 2), 1e-12))
    y = (1 - a.wet) * x + a.wet * wet
    peak = np.max(np.abs(y))
    if peak > 0.98:
        y *= 0.98 / peak
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                    "-c:a", "pcm_s24le", a.output], input=y.astype(np.float32).tobytes(), check=True)
    print(f"wrote {a.output}（残響 {a.rt}秒、響きの割合 {a.wet}）")


if __name__ == "__main__":
    main()
