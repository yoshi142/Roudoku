#!/usr/bin/env python3
"""読み直しを合図にした自動の切り詰めと、「、」「。」の間（ま）の長さそろえ。

本人の録り方（2026-10-23 の指示）：言い直すときは、手拍子をせずに同じ行を頭から読み直す。
この道具はそれを前提に、次を自動で行う。

1. 文字起こし（faster-whisper、単語ごとの時刻）。結果は <out>/words.json に保存し、2回目からは再利用する
2. 無音で区切った「句」（声が続いている区間）を作り、単語を始まりの時刻で句に割り当てる
3. 読み直しの判定：ある句の読みが、あと（40句以内、150秒以内）に始まる句（いくつか続けたもの）の頭と
   ほぼ同じで、あいだの句もすべてそのあとで読み直されているなら、その句は古い読みとして捨てる。最後の読みが残る。
   あいだの句の条件があるので、題名と本文の1行目が同じ（雨ニモマケズ）でも題名は捨てない
4. 句と句のあいだの間を「、」（短い）と「。」（長い）に分ける。台本に句読点がなくても、録音の間の長さと
   文字起こしの句読点から決める
5. 「、」の間と「。」の間をそれぞれ同じ長さにそろえて、つなぎ直す（既定 「、」1.0秒、「。」2.4秒）
6. 台本（--script）があれば、残した読みと台本の読みを仮名で比べ、違う箇所を「要確認」として書き出す

使い方:
  python3 tools/auto_edit.py narration/trial-01/raw/trial-01_take01.wav --out narration/trial-01/out/auto \\
      --script narration/trial-01/script.md [--model medium] [--comma 1.0] [--period 2.4]
出力（<out>/）:
  words.json      文字起こし（単語ごとの時刻）
  timeline.json   残した句が edited.wav の何秒にあるかと、台本の位置（字幕づくりに使う）
  phrases.tsv     句の一覧（開始、終了、文字、判定、後ろの間の種類）。手で直して --phrases で読み込み直せる
  report.md       判定の理由、台本との違い、統計
  edited.wav      切り詰めと間のそろえを済ませた音声（整音前、48kHz/24bit モノラル）
依存: faster-whisper、fugashi と unidic-lite（読みの判定。pip install --use-pep517 fugashi unidic-lite）、
      pykakasi（fugashi がないときの代わり）、numpy、ffmpeg
"""
import argparse, difflib, json, os, re, subprocess, sys
import numpy as np

SR = 48000


# ---------- 音声 ----------
def load(path, sr):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def speech_runs(a, sr, thr_db=None, min_gap=0.25, min_run=0.10):
    """10ms ごとの音量から、声のある区間を返す。閾値は録音ごとに自動で決める。"""
    f = sr // 100
    n = len(a) // f
    db = 20 * np.log10(np.sqrt((a[:n * f].reshape(n, f) ** 2).mean(1)) + 1e-9)
    if thr_db is None:
        thr_db = max(np.percentile(db, 95) - 25, np.percentile(db, 10) + 8)
    on = db > thr_db
    runs, i = [], 0
    while i < n:
        if on[i]:
            j = i
            while j < n and on[j]:
                j += 1
            runs.append([i / 100, j / 100])
            i = j
        else:
            i += 1
    merged = []
    for s, e in runs:
        if merged and s - merged[-1][1] < min_gap:
            merged[-1][1] = e
        else:
            merged.append([s, e])
    return [r for r in merged if r[1] - r[0] >= min_run], float(thr_db)


# ---------- 文字 ----------
_kks = None
KANJI_NUM = str.maketrans("0123456789", "〇一二三四五六七八九")


_tagger = None


def kana(text):
    """読みを平仮名で返す。fugashi（unidic-lite）があれば文脈で読みを決め、なければ pykakasi を使う。
    pykakasi は「陰」を「いん」と読むなど誤りが多かった（2026-10-23）。"""
    global _kks, _tagger
    text = re.sub(r"[\s、。，．,.！？!?「」『』（）()・…―\-]", "", text.translate(KANJI_NUM))  # 改行を含むと pykakasi が文字を重ねる
    if _tagger is None:
        try:
            import fugashi
            _tagger = fugashi.Tagger()
        except Exception:
            _tagger = False
    if _tagger:
        parts = []
        for w in _tagger(text):
            k = getattr(w.feature, "kana", None)
            parts.append(k if k and k != "*" else w.surface)
        h = "".join(parts)
    else:
        if _kks is None:
            import pykakasi
            _kks = pykakasi.kakasi()
        h = "".join(x["hira"] for x in _kks.convert(text))
    h = "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in h)  # カタカナ→ひらがな
    return re.sub(r"[^ぁ-ゖー一-龥]", "", h)


def sim(a, b):
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def contained(part, whole):
    """part が whole の中にどれだけ含まれるか（最長の共通部分 ÷ part の長さ）。"""
    if not part:
        return 1.0
    if not whole:
        return 0.0
    m = difflib.SequenceMatcher(None, whole, part, autojunk=False).find_longest_match(0, len(whole), 0, len(part))
    return m.size / len(part)


def script_hits(k, S, min_ratio=0.6):
    """句の仮名 k が台本の仮名 S のどこに当たるかの候補（開始、終了、一致率）。"""
    L = len(k)
    hits = []
    if L <= 3:  # 短い句は1字違いでも別の箇所に当たりやすいので、同じ長さ以上・高い一致だけ
        min_ratio = max(min_ratio, 0.8)
    for dl in ((0, 1) if L <= 3 else (0, -1, 1, -2, 2)):
        n = L + dl
        if n < 1:
            continue
        for st in range(0, max(1, len(S) - n + 1)):
            w = S[st:st + n]
            sm = difflib.SequenceMatcher(None, k, w, autojunk=False)
            if sm.real_quick_ratio() < min_ratio or sm.quick_ratio() < min_ratio:
                continue
            r = sm.ratio()
            if r >= min_ratio:
                hits.append((st, st + n, r))
    # 同じ場所の重なりは一致率の高いものだけ残す
    hits.sort(key=lambda x: -x[2])
    out = []
    for h in hits:
        if all(abs(h[0] - o[0]) > max(2, L // 3) for o in out):
            out.append(h)
    return out


HALLUCINATIONS = ["ご視聴ありがとうございました", "視聴ありがとうございました", "ご視聴ありがとうございます",
                  "チャンネル登録", "お願いします。", "おやすみなさい"]
COUNTERS = "日合年月人本回時分秒歳個つ番夜段章度里尺寸貫円銭"


def clean_words(words):
    """文字起こしのよく知られた誤りを除く（2026-10-23 の録り直しで確認）。
    - 録音の冒頭や無音に作られる「ご視聴ありがとうございました」など
    - 実際にはない数字（「222ほめられもせず」）。後ろに助数詞（日、合 など）が続かない数字だけの単語を除く"""
    text = "".join(w["w"] for w in words)
    drop = set()
    for h in HALLUCINATIONS:
        for m in re.finditer(re.escape(h.strip("。")), text):
            pos = 0
            for j, w in enumerate(words):
                if pos < m.end() and pos + len(w["w"]) > m.start():
                    drop.add(j)
                pos += len(w["w"])
    out = []
    for j, w in enumerate(words):
        t = w["w"].strip()
        if j in drop:
            continue
        if re.fullmatch(r"[0-9０-９]+", t):
            nxt = words[j + 1]["w"].strip() if j + 1 < len(words) else ""
            if not nxt or nxt[0] not in COUNTERS:
                continue
        out.append(w)
    return out


def transcribe(path, model, prompt, cache):
    if os.path.exists(cache):
        return json.load(open(cache, encoding="utf-8"))
    from faster_whisper import WhisperModel
    a16 = load(path, 16000)
    m = WhisperModel(model, device="cpu", compute_type="int8")
    segs, _ = m.transcribe(a16, language="ja", word_timestamps=True, initial_prompt=prompt or None,
                           condition_on_previous_text=False, vad_filter=False)
    words = [{"w": w.word, "s": round(w.start, 3), "e": round(w.end, 3)} for s in segs for w in s.words]
    json.dump(words, open(cache, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    return words


def script_text(path):
    """台本 md から読む本文だけを取り出す（【】指示、見出し、記号を除き、漢字（よみ）はよみにする）。"""
    t = open(path, encoding="utf-8").read()
    head = ""
    h = re.search(r"^#\s*台本：\s*(.+?)「(.+?)」", t, re.M)
    if h:
        head = h.group(2) + h.group(1) + "\n"  # 録音の冒頭で読む題名と作者名
    body = t
    m = re.search(r"##\s*\d*\s*　?朗読.*?\n(.*?)(?=\n##\s|\n---)", t, re.S)
    if m:
        body = m.group(1)
    body = re.sub(r"【[^】]*】", "", body)
    body = re.sub(r"[一-龥々ヶ]+（([ぁ-んー・]+)）", lambda x: x.group(1).replace("・", ""), body)
    body = re.sub(r"（[^）]*）", "", body)
    body = re.sub(r"^#.*$", "", body, flags=re.M)
    return head + body.replace("／", "")


# ---------- 本体 ----------
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", nargs="+", help="録音ファイル。複数なら録った順に並べる（あとのファイルの読みが優先される。録り直しの差し替えに使う）")
    ap.add_argument("--out", required=True)
    ap.add_argument("--script", help="台本 md（読みの比較と、文字起こしの手がかりに使う）")
    ap.add_argument("--model", default="medium")
    ap.add_argument("--comma", type=float, default=1.0, help="「、」の間（秒）。2026-10-23 に本人の指示で 0.6 から変更")
    ap.add_argument("--period", type=float, default=2.4, help="「。」の間（秒）。2026-10-23 に本人の指示で 1.5 から変更")
    ap.add_argument("--after_title", type=float, default=2.0, help="題名と作者名のあとの間（秒）。--keep_head のときだけ使う")
    ap.add_argument("--keep_head", action="store_true",
                    help="題名と作者名の読み上げを残す。既定では外し、本文から始める（本人の指示、2026-10-23）")
    ap.add_argument("--long_gap", type=float, default=None, help="この秒数以上の間は「。」とみなす（既定は録音から自動）")
    ap.add_argument("--min_gap", type=float, default=0.25, help="これより短い途切れは句の中とみなす")
    ap.add_argument("--thr_db", type=float, default=None, help="声とみなす音量（dB）。既定は自動")
    ap.add_argument("--lead", type=float, default=1.94, help="冒頭の無音（秒）。句の前の余白 0.06秒と合わせて、動画の開始から約2秒で朗読が始まる（本人の指示、2026-10-23）")
    ap.add_argument("--tail", type=float, default=2.5, help="末尾の無音（秒）")
    ap.add_argument("--phrases", help="手で直した phrases.tsv を読み込み、判定をやり直さずに音声だけ作る")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    # 複数のファイルは録った順に、3秒の無音をはさんでつなぐ。同じ箇所はあとの読みが選ばれる
    gap = np.zeros(3 * SR, np.float32)
    parts, offsets, pos = [], [], 0.0
    ref_lufs = None
    for i, f in enumerate(a.input):
        x = load(f, SR)
        # 2本目以降は1本目と同じ音量にそろえる（録り直しの行だけ声の大きさが変わらないように）
        r = subprocess.run(["ffmpeg", "-nostats", "-hide_banner", "-i", f, "-af", "ebur128", "-f", "null", "-"],
                           capture_output=True, text=True).stderr
        mm = re.findall(r"^\s+I:\s+(-?[\d.]+) LUFS", r, re.M)
        lu = float(mm[-1]) if mm else None
        if i == 0:
            ref_lufs = lu
        elif lu is not None and ref_lufs is not None:
            x = x * (10 ** ((ref_lufs - lu) / 20))
            print(f"{os.path.basename(f)}：{lu} LUFS → 1本目の {ref_lufs} LUFS にそろえた")
        offsets.append(pos)
        parts += ([gap] if i else []) + [x]
        pos += len(x) / SR + (3.0 if i < len(a.input) - 1 else 0)
    audio = np.concatenate(parts)
    dur = len(audio) / SR
    script = script_text(a.script) if a.script else ""
    prompt = re.sub(r"\s+", "", script)[:200] if script else ""

    if a.phrases:
        ph = []
        for line in open(a.phrases, encoding="utf-8"):
            if line.startswith("#") or line.startswith("start"):
                continue
            c = line.rstrip("\n").split("\t")
            ph.append({"s": float(c[0]), "e": float(c[1]), "text": c[2], "keep": c[3] == "残す",
                       "why": c[4] if len(c) > 4 else "", "punct": c[5] if len(c) > 5 else ""})
        thr = None
    else:
        words = []
        for i, f in enumerate(a.input):
            cache = os.path.join(a.out, "words.json" if i == 0 else f"words_{i + 1}.json")
            ws = clean_words(transcribe(f, a.model, prompt, cache))
            for w in ws:
                words.append({"w": w["w"], "s": w["s"] + offsets[i], "e": w["e"] + offsets[i], "file": i})
        runs, thr = speech_runs(audio, SR, a.thr_db, a.min_gap)
        ph = [{"s": s, "e": e, "text": "", "keep": True, "why": "", "punct": ""} for s, e in runs]
        # 単語は「始まりの時刻」で句に割り当てる。始まりが無音の中なら次の句へ。
        # 単語の終わりの時刻は後ろの無音に食い込みやすく、当てにならない（2026-10-23 の雨ニモマケズで確認）。
        # 句ごとに切り出して起こす方式も試したが、文脈がなく聞き違いが増えたので使わない
        for w in words:
            t = w["s"]
            tgt = next((p for p in ph if p["s"] - 0.03 <= t < p["e"]), None)
            if tgt is None:
                tgt = next((p for p in ph if p["s"] >= t), ph[-1])
            tgt["text"] += w["w"]
        for p in ph:
            p["text"] = p["text"].strip()
        skana = "".join(kana(l) for l in script.split("\n")) if script else ""  # 行ごとに仮名にしてつなぐ（字幕の行の位置とそろえる）
        for p in ph:
            k = kana(p["text"])
            if not k:
                p["keep"], p["why"] = False, "文字なし（息や物音）"
        live = [p for p in ph if p["keep"]]
        K = [kana(p["text"]) for p in live]
        if skana:
            # 台本あり：「録音の時間順に並べたとき、台本の位置も前へ戻らない」句の組み合わせのうち、
            # 台本を最も多く覆うものを選ぶ（動的計画法）。同じ箇所を覆う読みが複数あれば後の読みを選ぶ。
            # 1句ずつ決める方式は、短い句の判定の誤りが後ろに連鎖したので使わない（2026-10-23）
            def dp_choose(idxs):
                states = []  # (句の番号, 開始, 終了, 一致率, 累積値, 前の状態)
                for idx in idxs:
                    k = K[idx]
                    if len(k) <= 1:  # 1字の句は照合に使わない（断片や物音のことが多い）
                        continue
                    hits = script_hits(k, skana)
                    new = []
                    for st, en, r in hits:
                        # 0.75 以上の一致は同じ扱いにする（文字起こしの漢字の当て方「四合／4号」で古い読みが選ばれたため）。
                        # あとの読みを、覆う字数に比例して少しだけ優先する（句の数ではなく字数で。細切れの句が得をしないように）
                        q = 1.0 if r >= 0.75 else r
                        gain = (en - st) * ((q - 0.6) / 0.4) * (1 + 0.02 * idx / max(1, len(K)))
                        best, bp = 0.0, None
                        for si, sv in enumerate(states):
                            if sv[2] <= st and sv[4] > best:
                                best, bp = sv[4], si
                        new.append((idx, st, en, r, best + gain, bp))
                    states.extend(new)
                ch = {}
                if states:
                    si = max(range(len(states)), key=lambda i: states[i][4])
                    while si is not None:
                        idx, st, en, r, v, bp = states[si]
                        ch[idx] = (st, en, r)
                        si = bp
                return ch

            # 録音ファイルごとに台本の位置を決め、同じ箇所はあとのファイルの読みを優先する。
            # 録り直しは台本のどこからでもよく、どの順に録ってもよい（2026-10-23、冒頭だけの録り直しで対応）
            fidx = [max(i for i, o in enumerate(offsets) if p["s"] >= o - 0.01) for p in live]
            chosen, covered = {}, set()
            for f in range(len(a.input) - 1, -1, -1):
                ch = dp_choose([i for i in range(len(live)) if fidx[i] == f])
                mine = {}
                for idx, (st, en, r) in ch.items():
                    if sum(1 for x in range(st, en) if x in covered) >= 0.5 * (en - st):
                        continue  # あとのファイルで読み直している
                    mine[idx] = (st, en, r)
                for st, en, r in mine.values():
                    covered.update(range(st, en))
                chosen.update(mine)
            for idx, (p, k) in enumerate(zip(live, K)):
                if idx in chosen:
                    st, en, r = chosen[idx]
                    p["why"] = f"台本 {st}〜{en} 字目（一致 {r:.2f}）"
                    continue
                hits = script_hits(k, skana)
                # あとで読まれた句と台本の同じ箇所に当たるなら読み直し。そうでなければ台本にない読みとして残す
                # あとで残した句が台本の同じ箇所を覆っていれば読み直し
                later_cov = set()
                for j in chosen:
                    if j > idx or fidx[j] > fidx[idx]:
                        later_cov.update(range(chosen[j][0], chosen[j][1]))
                redo = [h for h in hits if sum(1 for x in range(h[0], h[1]) if x in later_cov) >= 0.7 * (h[1] - h[0])]
                near = any(abs(q["s"] - p["e"]) < 1.2 or abs(p["s"] - q["e"]) < 1.2
                           for j2, q in enumerate(live) if j2 in chosen)
                if redo:
                    p["keep"] = False
                    p["why"] = f"読み直し（台本 {redo[0][0]}字目からの箇所を、あとで読み直している）"
                elif not hits and len(k) <= 3 and near:
                    p["why"] = "短い句。隣の句とつながっているので残す"
                elif len(k) <= 1 or (not hits and len(k) <= 3):
                    p["keep"] = False
                    p["why"] = "台本にない短い音（物音や言いよどみと見られる）"
                else:
                    p["why"] = "台本にない読み（残す。要確認）"
            # 仕上げの並びは台本の順。台本に当たらない句は、同じファイルで直前に残した句のすぐあとに置く
            for idx, p in enumerate(live):
                if idx in chosen:
                    p["spos"] = (chosen[idx][0], 0, idx)
                else:
                    prev = [j for j in chosen if fidx[j] == fidx[idx] and j < idx]
                    nxt = [j for j in chosen if fidx[j] == fidx[idx] and j > idx]
                    if prev:
                        p["spos"] = (chosen[max(prev)][0], 1, idx)
                    elif nxt:
                        p["spos"] = (chosen[min(nxt)][0], -1, idx)
                    else:
                        p["spos"] = (10 ** 9, 0, idx)
            # 残した句と句のあいだにある「残さなかった句」の並びに読み直しが1つでもあれば、並び全体を読み直しとみなす
            # （文字起こしが「わか」を「分か」と書き「ぶんか」と読まれるなど、台本に当たらない断片が残るのを防ぐ）
            run = []
            for idx in range(len(live) + 1):
                if idx == len(live) or idx in chosen:
                    if any(q["why"].startswith("読み直し") for q in run):
                        for q in run:
                            if q["keep"] and not script_hits(kana(q["text"]), skana):
                                q["keep"] = False
                                q["why"] = "読み直し（前後の読み直しと一続き）"
                    run = []
                else:
                    run.append(live[idx])
        else:
          # 台本なし：句 i の読みが、あとの句 j から始まる読みの頭と一致し、
          # かつ i と j のあいだの句もすべて j のあとで読み直されているとき、i は古い読み
          for i, p in enumerate(live):
            ki = K[i]
            if len(ki) < 2:
                continue
            for j in range(i + 1, min(i + 40, len(live))):
                if live[j]["s"] - p["e"] > 150:
                    break
                cont = "".join(K[j:j + (j - i) + 12])
                r = sim(ki, cont[:len(ki)])
                if r < 0.72:
                    continue
                if all(contained(K[q], cont) >= 0.7 for q in range(i + 1, j)):
                    p["keep"] = False
                    p["why"] = f"読み直し（{live[j]['s']:.1f}秒からの読みと一致 {r:.2f}）"
                    break
        # 間の種類：後ろの間の長さ（本人が次に声を出すまで）と、文字起こしの句読点から
        kept = [p for p in ph if p["keep"]]
        gaps = []
        for p in kept:
            nxt = [q for q in ph if q["s"] > p["e"] and kana(q["text"])]
            p["gap"] = (nxt[0]["s"] - p["e"]) if nxt else None
            if p["gap"] is not None:
                gaps.append(p["gap"])
        # 「。」の境は録音ファイルごとに決める（録った日や読み方で間の取り方が変わるため）
        file_of = lambda t: max(i for i, o in enumerate(offsets) if t >= o - 0.01)
        if len(a.input) > 1 and a.long_gap is None:
            # 1本目の終わりの句の「後ろの間」はファイルのつなぎ目（3秒）を含むので数えない
            per = {}
            for fi in range(len(a.input)):
                g = np.log(np.array([p["gap"] for p in kept if p["gap"] is not None and file_of(p["s"]) == fi] or [1.5]))
                best, lg = -1, 1.5
                if len(g) >= 4:
                    for t in np.linspace(g.min(), g.max(), 60)[1:-1]:
                        lo, hi = g[g < t], g[g >= t]
                        if len(lo) and len(hi):
                            v = len(lo) * len(hi) * (lo.mean() - hi.mean()) ** 2
                            if v > best:
                                best, lg = v, float(np.exp(t))
                per[fi] = min(max(lg, 1.0), 3.0)
            for p in kept:
                last = p["text"].strip()[-1:] if p["text"].strip() else ""
                if p["gap"] is None:
                    p["punct"] = "終"
                else:
                    # 文字起こしが付けた句読点を先に使う（抑揚と文のつながりから付く）。なければ間の長さで決める
                    p["punct"] = last if last in "、。" and last else ("。" if p["gap"] >= per[file_of(p["s"])] else "、")
            print("「。」の境（ファイルごと）:", {a.input[k]: round(v, 2) for k, v in per.items()})
            long_gap = "ファイルごと"
        elif a.long_gap is not None:
            long_gap = a.long_gap
        elif len(gaps) >= 4:
            g = np.log(np.array(gaps))
            # 2つの群に分ける（大津の方法）。録音ごとに本人の間の取り方に合わせる
            best, long_gap = -1, 1.5
            for t in np.linspace(g.min(), g.max(), 60)[1:-1]:
                lo, hi = g[g < t], g[g >= t]
                if len(lo) == 0 or len(hi) == 0:
                    continue
                v = len(lo) * len(hi) * (lo.mean() - hi.mean()) ** 2
                if v > best:
                    best, long_gap = v, float(np.exp(t))
            long_gap = min(max(long_gap, 1.0), 3.0)
        else:
            long_gap = 1.5
        for p in ([] if long_gap == "ファイルごと" else kept):
            last = p["text"].strip()[-1:] if p["text"].strip() else ""
            if p["gap"] is None:
                p["punct"] = "終"
            elif last in ("、", "。"):
                p["punct"] = last  # 文字起こしが付けた句読点を先に使う
            elif p["gap"] >= long_gap:
                p["punct"] = "。"
            else:
                p["punct"] = "、"
        a.long_gap = long_gap
        if skana and script.startswith(script.split("\n", 1)[0]) and "\n" in script:
            hl = len(kana(script.split("\n", 1)[0]))
            for p in kept:
                m = re.search(r"台本 (\d+)〜(\d+) 字目", p["why"])
                if m and int(m.group(2)) <= hl + 1:
                    last_head = p
            if "last_head" in locals():
                last_head["punct"] = "題"

    # 題名と作者名の読み上げは外し、本文から始める（本人の指示、2026-10-23）。照合には使うので、ここで外す
    if not a.phrases and skana and not a.keep_head:
        hl = len(kana(script.split("\n", 1)[0]))
        for p in ph:
            m = re.search(r"台本 (\d+)〜(\d+) 字目", p["why"])
            if p["keep"] and m and int(m.group(2)) <= hl + 1:
                p["keep"] = False
                p["why"] = "題名と作者名（動画は本文から始める）"
    kept = [p for p in ph if p["keep"]]
    if not kept:
        sys.exit("残す句がありません")
    if all("spos" in p for p in kept):
        kept.sort(key=lambda p: p["spos"])  # 台本の順に並べる（録り直しのファイルの順に左右されない）
    for p in kept[:-1]:
        if p["punct"] == "終":
            p["punct"] = "。"  # ファイルの最後の句でも、仕上げの途中なら「。」の間
    kept[-1]["punct"] = "終"

    # phrases.tsv
    with open(os.path.join(a.out, "phrases.tsv"), "w", encoding="utf-8") as f:
        f.write("# 判定を直すときは 4列目（残す／捨てる）と 6列目（、／。）を書き換え、--phrases で読み込む\n")
        f.write("start\tend\ttext\tdecision\twhy\tpunct\n")
        for p in ph:
            f.write(f"{p['s']:.2f}\t{p['e']:.2f}\t{p['text']}\t{'残す' if p['keep'] else '捨てる'}\t{p['why']}\t{p['punct']}\n")

    # 音声をつなぎ直す
    pre, post, fade = 0.06, 0.18, 0.012
    out = [np.zeros(int(a.lead * SR), np.float32)]
    t_out = a.lead
    timeline = []
    for k, p in enumerate(kept):
        s = max(0.0, p["s"] - pre)
        e = min(dur, p["e"] + post)
        seg = audio[int(s * SR):int(e * SR)].copy()
        nf = int(fade * SR)
        if len(seg) > 2 * nf:
            seg[:nf] *= np.linspace(0, 1, nf)
            seg[-nf:] *= np.linspace(1, 0, nf)
        out.append(seg)
        m = re.search(r"台本 (\d+)〜(\d+) 字目", p["why"])
        timeline.append({"src_s": p["s"], "src_e": p["e"], "out_s": round(t_out + (p["s"] - s), 3),
                         "out_e": round(t_out + (p["e"] - s), 3), "text": p["text"], "punct": p["punct"],
                         "script": [int(m.group(1)), int(m.group(2))] if m else None})
        t_out += len(seg) / SR
        if p["punct"] == "終":
            z = np.zeros(int(a.tail * SR), np.float32)
        else:
            pause = {"、": a.comma, "。": a.period, "題": a.after_title}.get(p["punct"], a.period)
            z = np.zeros(int(max(0.05, pause - pre - post) * SR), np.float32)
        out.append(z)
        t_out += len(z) / SR
    y = np.concatenate(out)
    json.dump({"inputs": a.input, "offsets": offsets, "script": a.script, "phrases": timeline},
              open(os.path.join(a.out, "timeline.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    wav = os.path.join(a.out, "edited.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                    "-c:a", "pcm_s24le", wav], input=y.tobytes(), check=True)

    # 台本との比較
    diffs = []
    if script:
        said = kana("".join(p["text"] for p in kept))
        want = "".join(kana(l) for l in script.split("\n"))
        sm = difflib.SequenceMatcher(None, want, said, autojunk=False)
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            if op == "equal":
                continue
            ctx = want[max(0, i1 - 6):i1]
            diffs.append((op, ctx, want[i1:i2], said[j1:j2]))

    # report.md
    n_drop = sum(1 for p in ph if not p["keep"])
    with open(os.path.join(a.out, "report.md"), "w", encoding="utf-8") as f:
        f.write(f"# 自動編集の記録\n\n入力：{"、".join(a.input)}（つないで {dur:.1f}秒）\n\n")
        f.write(f"- 句：{len(ph)}（残す {len(kept)}、捨てる {n_drop}）\n")
        f.write(f"- 声とみなした音量：{thr if thr is None else round(thr, 1)} dB　句の中とみなす途切れ：{a.min_gap}秒未満\n")
        f.write(f"- 「。」とみなした間：{a.long_gap if a.long_gap else '（phrases.tsv の指定）'}秒以上（録音から自動）\n")
        f.write(f"- そろえた間：「、」{a.comma}秒、「。」{a.period}秒、題名のあと {a.after_title}秒\n")
        f.write(f"- 仕上がり：{len(y) / SR:.1f}秒\n\n")
        f.write("## 残した読み\n\n")
        for p in kept:
            f.write(f"- {p['s']:7.2f}　{p['text']}　〔{p['punct']}〕\n")
        f.write("\n## 捨てた区間\n\n")
        for p in ph:
            if not p["keep"]:
                f.write(f"- {p['s']:7.2f}　{p['text'] or '（文字なし）'}　… {p['why']}\n")
        if script:
            f.write("\n## 台本との違い（要確認。仮名に直して比べた機械的な結果で、文字起こしや仮名変換の誤りも含む）\n\n")
            f.write("| 直前 | 台本 | 録音 |\n|------|------|------|\n")
            for op, ctx, w, s in diffs:
                f.write(f"| …{ctx} | {w or '（なし）'} | {s or '（なし）'} |\n")
    print(f"句 {len(ph)}（残す {len(kept)}、捨てる {n_drop}）、「。」の境 {a.long_gap}秒 → {wav}（{len(y) / SR:.1f}秒）")
    print(f"記録: {os.path.join(a.out, 'report.md')}")


if __name__ == "__main__":
    main()
