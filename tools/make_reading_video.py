#!/usr/bin/env python3
"""朗読の動画を作る：背景（静止画）＋整音済みの声＋字幕（ASS、画面中央）＋静かな音楽や環境音。

音楽・環境音は物語に合わせて選ぶ（本人の指示、2026-10-23。例：雨ニモマケズは雨の音）。選び方は docs/knowhow.md。

- 音楽は声より --music_lu（既定 20）LU 小さくし、声が出ているあいだはさらに少し下げる（ダッキング）
- 音楽は冒頭 3秒でフェードイン、終わり 5秒でフェードアウト。曲が短ければ繰り返す
- 映像は冒頭 1.2秒を黒からフェードイン、終わり 2秒でフェードアウト
- 仕上げにリミッター（-1.5 dBFS）。音量は声の整音（-16 LUFS 前後）とほぼ同じになる

- --bg_changes で、途中から背景を替えられる（例：枕草子の春・夏・秋・冬）。「画像@秒」をカンマで並べる。
  切り替えは --bg_fade 秒（既定 1.5）のクロスフェード。--bg は最初の背景として使う

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
    ap.add_argument("--ambient", help="環境音（雨、川、虫の声など）。音楽と重ねても、単独でもよい")
    ap.add_argument("--ambient_lu", type=float, default=20.0, help="環境音を声より何 LU 小さくするか")
    ap.add_argument("--ambient_duck_db", type=float, default=2.0, help="声のあいだ環境音を何 dB 下げるか（大きく下げると不自然）")
    ap.add_argument("--ambient_start", type=float, default=0.0, help="環境音の何秒目から使うか（冒頭の無音を飛ばす）")
    ap.add_argument("--bg_changes", help="途中で替える背景。「画像@開始秒,画像@開始秒」（--bg は 0秒から）")
    ap.add_argument("--end_fade", type=float, default=6.0, help="終わりに音楽・環境音を消すフェードの長さ（秒）。読み終わったあとも少し残してから、ゆっくり消す（本人の指示、2026-10-23）")
    ap.add_argument("--video_end_fade", type=float, default=3.0, help="終わりに映像を暗くするフェードの長さ（秒）")
    ap.add_argument("--bg_fade", type=float, default=1.5, help="背景の切り替えのクロスフェード（秒）")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    dur = duration(a.voice)
    v_lufs = loudness(a.voice)
    vf = f"fade=t=in:st=0:d=1.2,fade=t=out:st={dur - a.video_end_fade:.2f}:d={a.video_end_fade}"
    if a.ass:
        ass = os.path.relpath(a.ass).replace(":", r"\:")
        vf = f"subtitles={ass}:fontsdir={os.path.relpath(os.path.join(TOOLS, 'fonts'))}," + vf
    vf += ",format=yuv420p"

    if a.bg_changes:
        # 背景ごとに静止画を流し、xfade でつないだ背景の動画を先に作る
        segs = [(a.bg, 0.0)] + [(x.rsplit("@", 1)[0], float(x.rsplit("@", 1)[1])) for x in a.bg_changes.split(",")]
        F = a.bg_fade
        offs = [st - F / 2 for _, st in segs[1:]]
        bcmd, chain = ["ffmpeg", "-y", "-v", "error"], []
        for i, (img, st) in enumerate(segs):
            start = 0.0 if i == 0 else offs[i - 1]
            end = (offs[i] + F) if i < len(offs) else dur
            bcmd += ["-loop", "1", "-framerate", "30", "-t", f"{end - start:.3f}", "-i", img]
        prev = "[0:v]"
        for i, o in enumerate(offs):
            out = f"[x{i}]"
            chain.append(f"{prev}[{i + 1}:v]xfade=transition=fade:duration={F}:offset={o:.3f}{out}")
            prev = out
        bg_video = os.path.splitext(a.out)[0] + "_bg.mp4"
        bcmd += ["-filter_complex", ";".join(chain), "-map", prev, "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                 "-pix_fmt", "yuv420p", "-r", "30", "-t", f"{dur:.3f}", bg_video]
        subprocess.run(bcmd, check=True)
        print("背景の切り替え:", ", ".join(f"{os.path.basename(img)}@{st:g}秒" for img, st in segs))
        cmd = ["ffmpeg", "-y", "-v", "error", "-i", bg_video, "-i", a.voice]
    else:
        cmd = ["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", "30", "-t", f"{dur:.3f}", "-i", a.bg, "-i", a.voice]
    layers = []  # (ファイル, 声より何LU小さく, ダッキング dB, 開始秒)
    if a.music:
        layers.append((a.music, a.music_lu, a.duck_db, a.music_start))
    if a.ambient:
        layers.append((a.ambient, a.ambient_lu, a.ambient_duck_db, a.ambient_start))
    if layers:
        n = len(layers)
        parts = [f"[1:a]aformat=sample_rates=48000:channel_layouts=stereo,asplit={n + 1}[v]" + "".join(f"[sc{i}]" for i in range(n))]
        mixed = []
        for i, (f, lu, duck, st) in enumerate(layers):
            m_lufs = loudness(f) or -20.0
            gain = (v_lufs - lu) - m_lufs
            cmd += ["-stream_loop", "-1", "-ss", str(st), "-i", f]
            ratio = max(1.5, 10 ** (duck / 20) * 2)
            parts.append(f"[{i + 2}:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim=0:{dur:.3f},asetpts=PTS-STARTPTS,"
                         f"volume={gain:.2f}dB,afade=t=in:st=0:d=3,afade=t=out:st={dur - a.end_fade:.2f}:d={a.end_fade}[l{i}]")
            parts.append(f"[l{i}][sc{i}]sidechaincompress=threshold=0.02:ratio={ratio:.1f}:attack=80:release=600:makeup=1[d{i}]")
            mixed.append(f"[d{i}]")
            print(f"{os.path.basename(f)}：{m_lufs} LUFS → {gain:+.1f} dB（声より {lu} LU 小さく、声のあいだ約 {duck} dB 下げる）")
        parts.append("[v]" + "".join(mixed) + f"amix=inputs={n + 1}:duration=first:normalize=0,alimiter=limit=0.84:level=false[a]")
        cmd += ["-filter_complex", ";".join(parts) + f";[0:v]{vf}[vv]", "-map", "[vv]", "-map", "[a]"]
    else:
        cmd += ["-vf", vf, "-map", "0:v", "-map", "1:a"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-tune", "stillimage", "-r", "30",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", a.out]
    subprocess.run(cmd, check=True)
    print(f"wrote {a.out}（{duration(a.out):.1f}秒、音量 {loudness(a.out)} LUFS）")


if __name__ == "__main__":
    main()
