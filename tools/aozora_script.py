#!/usr/bin/env python3
"""青空文庫の XHTML から朗読台本（script.md）を作る。

- ルビは「漢字（よみ）」に直す。読点・句点の位置に「／」、段落の切れ目に「／／」を入れる
- --start/--end で、詩集などから一篇だけを切り出す（本文中の文字列で指定。end は含まない）
- --intro/--outro の文は読まない（本人の指示、2026-10-23：冒頭の紹介とおわりの語りはやめた）。渡すと、説明文用の参考として台本の末尾に残る。--extra で補足（Markdown）を末尾に足す
- 文字数（読み・記号・指示を除く）を数えて見出しに書く

使い方:
  python3 tools/aozora_script.py --src <XHTML の URL か ファイル> --title 蜘蛛の糸 --author 芥川龍之介 \
      --card https://www.aozora.gr.jp/cards/000879/card92.html --biblio "底本：..." \
      --intro intro.md --outro outro.md --out narration/trial-05-kumonoito/script.md
"""
import argparse, html, os, re, subprocess, sys, tempfile


def fetch(src):
    if re.match(r'https?://', src):
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.html').name
        subprocess.run(['curl', '-sS', '-L', '--max-time', '60', '-o', tmp, src], check=True)
        src = tmp
    raw = open(src, 'rb').read()
    for enc in ('shift_jis', 'utf-8'):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode('shift_jis', errors='replace')


def main_text(s):
    m = re.search(r'<div class="main_text">(.*?)<div class="bibliographical_information">', s, re.S)
    if not m:
        sys.exit('main_text が見つかりません')
    t = m.group(1)
    t = re.sub(r'<ruby><rb>(.*?)</rb><rp>（</rp><rt>(.*?)</rt><rp>）</rp></ruby>', r'\1（\2）', t)
    t = re.sub(r'<br\s*/>', '\n', t)
    t = re.sub(r'<img[^>]*alt="※\((.*?)\)"[^>]*/>', r'※［\1］', t)
    t = re.sub(r'<span class="notes">(.*?)</span>', r'\1', t)
    t = re.sub(r'<[^>]+>', '', t)
    t = html.unescape(t)
    return t.replace('\r', '')


GAIJI = {
    '※［「特のへん＋廴＋聿」、第3水準1-87-71］': '犍',   # 蜘蛛の糸「犍陀多」
    '※［「「蔭」の「陰のつくり」に代えて「人がしら／髟のへん」、第4水準2-86-78］': '蔭',
}


def to_script(t, poem=False):
    for k, v in GAIJI.items():
        t = t.replace(k, v)
    paras = [p.strip('　 \t') for p in t.split('\n')]
    out, blank = [], 0
    for p in paras:
        if not p:
            blank += 1
            continue
        if poem:
            # 詩：1行ごとに「／」、空行で「／／」
            if blank >= 1 and out:
                out[-1] = out[-1].rstrip('／') + '／／'
            out.append(p + '／')
        else:
            q = p.replace('、', '、／').replace('。', '。／')
            q = re.sub(r'。／([」』）])', r'。\1', q)   # 「〜。」の閉じかっこは句点の直後に
            q = re.sub(r'([」』])／?$', r'\1', q)
            q = re.sub(r'／+$', '', q)
            # 会話だけの短い段落は短い間、地の文は長い間
            out.append(q + ('／' if re.match(r'^[「『].*[」』]$', q) else '／／'))
        blank = 0
    return '\n'.join(out)


def count(s):
    s = re.sub(r'（[^）]*）|【[^】]*】|［[^］]*］', '', s)
    s = re.sub(r'^#.*$', '', s, flags=re.M)
    return len(re.sub(r'[／\s]', '', s))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True); ap.add_argument('--title', required=True); ap.add_argument('--author', required=True)
    ap.add_argument('--card', required=True); ap.add_argument('--biblio', default='')
    ap.add_argument('--start', default=None, help='切り出し開始（この文字列から）'); ap.add_argument('--end', default=None, help='切り出し終了（この文字列の手前まで）')
    ap.add_argument('--poem', action='store_true', help='詩として扱う（行ごとに間）')
    ap.add_argument('--intro', default=None); ap.add_argument('--outro', default=None); ap.add_argument('--extra', default=None)
    ap.add_argument('--heading', default='朗読'); ap.add_argument('--trial', default='')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    t = main_text(fetch(a.src))
    if a.start:
        i = t.find(a.start)
        if i < 0: sys.exit(f'start が見つかりません: {a.start}')
        t = t[i:]
    if a.end:
        j = t.find(a.end)
        if j < 0: sys.exit(f'end が見つかりません: {a.end}')
        t = t[:j]
    body = to_script(t, poem=a.poem)
    intro = open(a.intro, encoding='utf-8').read().strip() if a.intro else ''
    outro = open(a.outro, encoding='utf-8').read().strip() if a.outro else ''
    extra = open(a.extra, encoding='utf-8').read().strip() if a.extra else ''
    # 冒頭の紹介は読まない（本人の判断、2026-10-23）。--intro の文は説明文用に台本の末尾へ残す
    intro_note = ''.join(f'\n## 参考：{h}（読まない。説明文に使える）\n\n{t}\n' for h, t in [('紹介', intro), ('おわりの文', outro)] if t)
    n_body, n_total = count(body), count(body) + count(a.title) + count(a.author)
    rate = 250 if a.poem else 300
    est = n_total / rate
    md = f'''# 台本：{a.author}「{a.title}」{('（' + a.trial + '）') if a.trial else ''}

Ver.1.0　作成日：2026-10-22　作成：AI　読み手：本人

## 読み方の記号

- 「／」　短い間（息ひとつ分）。読点・句点（詩は行末）に機械的に入れてある。読み手の判断で詰めてよい
- 「／／」　長い間（段落の切れ目）
- （　）　読み。読まない。青空文庫のルビをそのまま使った
- 【　】　録音のときの指示。読まない

想定尺：約{est:.0f}〜{est * 1.3:.0f}分（本文 約{n_body:,}字、読みと指示を除く）

---

## 1　題名と作者　【本文と同じ声で。挨拶や紹介はせず、すぐ本文に入る】

{a.title}。／{a.author}。／／

【1秒、黙る】

## 2　{a.heading}　【ここから本文。急がない】

{body}

【読み終えたら3秒黙って、録音を止める。おわりの語りは読まない】

---

{extra}
{intro_note}
## 出典

{a.author}「{a.title}」青空文庫　{a.card}
{a.biblio}
図書カードに「著作権存続」の表示なし（2026-10-22 確認）
'''
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    open(a.out, 'w', encoding='utf-8').write(md)
    print(f'wrote {a.out}  本文{n_body}字 合計{n_total}字 想定{est:.1f}分')


if __name__ == '__main__':
    main()
