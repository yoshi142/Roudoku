#!/usr/bin/env python3
"""朗読の動画を作る：背景（静止画）＋整音済みの声＋字幕（ASS、画面中央）＋静かな音楽。

- 音楽は声より --music_lu（既定 20）LU 小さくし、声が出ているあいだはさらに少し下げる（ダッキング）
- 音楽は冒頭 3秒でフェードイン、終わり 5秒でフェードアウト。曲が短ければ繰り返す
- 映像は冒頭 1.2秒を黒からフェードイン、終わり 2秒でフェードアウト
- 仕上げにリミッター（-1.5 dBFS）。音量は声の整音（-16 LUFS 前後）とほぼ同じになる

使い方:
  python3 tools/make_reading_video.py --bg narration/trial-01/out/video_bg.png \\
      --voice narration/trial-01/out/trial-01_mastered.wav --ass narration/trial-01/out/subtitles.ass \\
      --music tools/music/<曲> --out narration/trial-01/out/trial-01.mp4
"""
import argparse, os, re, subprocess

TOOLS = os.path.dirname(os.path.abspath(__file__))


def duration(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                                capture_output=True, text=True, check=True).stdout.strip())


def loudness(p):
    r = subprocess.run(["ffmpeg", "-nostats", "-hide_banner", "-i", p, "-af", "ebur128", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    m = re.findall(r"^\s+I:\s+(-?[\d.]+) LUFS", r, re.M)
    return float(m[-1]) if m else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bg", required=True); ap.add_argument("--voice", required=True)
    ap.add_argument("--ass"); ap.add_argument("--music")
    ap.add_argument("--music_lu", type=float, default=20.0, help="音楽を声より何 LU 小さくするか")
    ap.add_argument("--duck_db", type=float, default=4.0, help="声が出ているあいだ、音楽をさらに何 dB 下げるか")
    ap.add_argument("--music_start", type=float, default=0.0, help="曲の何秒目から使うか")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    dur = duration(a.voice)
    v_lufs = loudness(a.voice)
    vf = f"fade=t=in:st=0:d=1.2,fade=t=out:st={dur - 2.0:.2f}:d=2.0"
    if a.ass:
        ass = os.path.relpath(a.ass).replace(":", r"\:")
        vf = f"subtitles={ass}:fontsdir={os.path.relpath(os.path.join(TOOLS, 'fonts'))}," + vf
    vf += ",format=yuv420p"

    cmd = ["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", "30", "-t", f"{dur:.3f}", "-i", a.bg, "-i", a.voice]
    if a.music:
        m_lufs = loudness(a.music) or -20.0
        gain = (v_lufs - a.music_lu) - m_lufs
        cmd += ["-stream_loop", "-1", "-ss", str(a.music_start), "-i", a.music]
        ratio = 10 ** (a.duck_db / 20) * 2  # だいたい duck_db 下がる程度の圧縮比
        af = (f"[2:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim=0:{dur:.3f},asetpts=PTS-STARTPTS,"
              f"volume={gain:.2f}dB,afade=t=in:st=0:d=3,afade=t=out:st={dur - 5:.2f}:d=5[m];"
              f"[1:a]aformat=sample_rates=48000:channel_layouts=stereo,asplit=2[v][sc];"
              f"[m][sc]sidechaincompress=threshold=0.02:ratio={ratio:.1f}:attack=80:release=600:makeup=1[md];"
              f"[v][md]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.84:level=false[a]")
        cmd += ["-filter_complex", af + f";[0:v]{vf}[vv]", "-map", "[vv]", "-map", "[a]"]
        print(f"声 {v_lufs} LUFS、音楽 {m_lufs} LUFS → {gain:+.1f} dB（声より {a.music_lu} LU 小さく）")
    else:
        cmd += ["-vf", vf, "-map", "0:v", "-map", "1:a"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-tune", "stillimage", "-r", "30",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", a.out]
    subprocess.run(cmd, check=True)
    print(f"wrote {a.out}（{duration(a.out):.1f}秒、音量 {loudness(a.out)} LUFS）")


if __name__ == "__main__":
    main()
