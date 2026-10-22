#!/usr/bin/env python3
"""faster-whisper で日本語の文字起こしを行い、時刻付きの行とTSVを出す。

言い直しの切り詰め（どこから読み直したか）を決めるために使う。字幕（SRT）の下書きも出せる。
使い方:
  python3 tools/transcribe.py input.wav --out narration/trial-01/out/transcript [--model small|medium]
出力: <out>.txt（時刻付きの行）、<out>.tsv（start, end, text）、<out>.srt
依存: pip install faster-whisper（初回はモデルを Hugging Face から取得する。small 約460MB、medium 約1.5GB）
注意: この環境の av ライブラリの版の都合で、音声は ffmpeg で読み込んで配列として渡す。
"""
import argparse, os, subprocess, sys
import numpy as np


def load16k(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def fmt(t):
    h, r = divmod(t, 3600); m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}".replace(".", ",")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input"); ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="small")
    ap.add_argument("--initial_prompt", default="", help="台本の冒頭などを渡すと固有名詞の認識が安定する")
    a = ap.parse_args()
    from faster_whisper import WhisperModel
    model = WhisperModel(a.model, device="cpu", compute_type="int8")
    segs, info = model.transcribe(load16k(a.input), language="ja", vad_filter=True,
                                  word_timestamps=True, initial_prompt=a.initial_prompt or None)
    segs = list(segs)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out + ".txt", "w", encoding="utf-8") as ft, open(a.out + ".tsv", "w", encoding="utf-8") as fv, \
            open(a.out + ".srt", "w", encoding="utf-8") as fs:
        fv.write("start\tend\ttext\n")
        for i, s in enumerate(segs, 1):
            ft.write(f"[{s.start:7.2f} - {s.end:7.2f}] {s.text.strip()}\n")
            fv.write(f"{s.start:.3f}\t{s.end:.3f}\t{s.text.strip()}\n")
            fs.write(f"{i}\n{fmt(s.start)} --> {fmt(s.end)}\n{s.text.strip()}\n\n")
    print(f"segments: {len(segs)} → {a.out}.txt / .tsv / .srt")


if __name__ == "__main__":
    main()
