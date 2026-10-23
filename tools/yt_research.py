#!/usr/bin/env python3
"""YouTube の朗読動画を検索し、再生数・投稿日・登録者数を集め、サムネイルの一覧画像を作る。

docs/thumbnail-research.md の調査（2026-10-23）を再現・更新するための道具。
依存: pip install yt-dlp（無料）。Pillow。
注意:
- 動画ごとの詳細取得は回数制限（HTTP 429、「bot ではないことを確認」）にかかりやすい。--detail は少なめに、間を空けて実行する
- 他の制作者のサムネイル画像は調査用に作業フォルダへ保存するだけにし、リポジトリには入れない

使い方:
  python3 tools/yt_research.py search --out WORKDIR --n 40 "朗読 宮沢賢治" "蜘蛛の糸 朗読"
  python3 tools/yt_research.py detail --out WORKDIR --top 150          # 再生上位の詳細（投稿日など）
  python3 tools/yt_research.py channels --out WORKDIR --top 60         # 登録者数
  python3 tools/yt_research.py sheet --out WORKDIR --query "蜘蛛の糸 朗読" --name kumo   # 同じ作品の上位8・下位8
"""
import argparse, datetime, json, os, subprocess, sys, time


def ytdlp(args):
    r = subprocess.run(['yt-dlp', *args], capture_output=True, text=True)
    return r.stdout


def cmd_search(a):
    os.makedirs(a.out, exist_ok=True)
    rows = {}
    path = os.path.join(a.out, 'videos.json')
    if os.path.exists(path):
        rows = {r['id']: r for r in json.load(open(path, encoding='utf-8'))}
    for q in a.queries:
        out = ytdlp(['--flat-playlist', '-j', '--extractor-args', 'youtube:lang=ja', f'ytsearch{a.n}:{q}'])
        for line in out.splitlines():
            d = json.loads(line)
            r = rows.setdefault(d['id'], dict(id=d['id'], title=d.get('title'), ch=d.get('channel') or d.get('uploader'),
                                              chid=d.get('channel_id'), views=d.get('view_count') or 0,
                                              dur=d.get('duration') or 0, qs=[]))
            if q not in r['qs']:
                r['qs'].append(q)
        print(q, len(rows), flush=True)
        time.sleep(1)
    json.dump(sorted(rows.values(), key=lambda r: -r['views']), open(path, 'w', encoding='utf-8'), ensure_ascii=False)


def cmd_detail(a):
    V = json.load(open(os.path.join(a.out, 'videos.json'), encoding='utf-8'))
    md = os.path.join(a.out, 'meta'); os.makedirs(md, exist_ok=True)
    for r in V[:a.top]:
        p = os.path.join(md, r['id'] + '.json')
        if os.path.exists(p) and os.path.getsize(p) > 0:
            continue
        out = ytdlp(['-j', '--skip-download', '--extractor-args', 'youtube:lang=ja', 'https://www.youtube.com/watch?v=' + r['id']])
        open(p, 'w', encoding='utf-8').write(out)
        if not out:
            print('失敗（回数制限の可能性）', r['id'], flush=True); time.sleep(20)
        time.sleep(2)


def cmd_channels(a):
    V = json.load(open(os.path.join(a.out, 'videos.json'), encoding='utf-8'))
    tot = {}
    for r in V:
        if r.get('chid'):
            tot[r['chid']] = tot.get(r['chid'], 0) + r['views']
    p = os.path.join(a.out, 'channels.json')
    subs = json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}
    for cid, _ in sorted(tot.items(), key=lambda x: -x[1])[:a.top]:
        if cid in subs:
            continue
        out = ytdlp(['--flat-playlist', '-J', '--playlist-end', '1', f'https://www.youtube.com/channel/{cid}/videos'])
        try:
            d = json.loads(out); subs[cid] = dict(name=d.get('channel'), subs=d.get('channel_follower_count'))
            print(subs[cid], flush=True)
        except Exception:
            print('失敗', cid)
        time.sleep(1)
    json.dump(subs, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def thumb(workdir, vid):
    d = os.path.join(workdir, 'th'); os.makedirs(d, exist_ok=True)
    p = os.path.join(d, vid + '.jpg')
    if not os.path.exists(p) or os.path.getsize(p) < 2000:
        for q in ['maxresdefault', 'sddefault', 'hqdefault']:
            subprocess.run(['curl', '-sS', '--max-time', '20', '-o', p, f'https://i.ytimg.com/vi/{vid}/{q}.jpg'])
            if os.path.getsize(p) > 2000:
                break
    return p


def cmd_sheet(a):
    from PIL import Image, ImageDraw, ImageFont
    V = json.load(open(os.path.join(a.out, 'videos.json'), encoding='utf-8'))
    rs = sorted([r for r in V if a.query in r['qs']], key=lambda r: -r['views'])
    items = [('上', r) for r in rs[:8]] + [('下', r) for r in rs[-8:]]
    F = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts', 'ipaexg.ttf')
    w, h, lab, cols = 480, 270, 58, 4
    rows = (len(items) + cols - 1) // cols
    S = Image.new('RGB', (cols * w, rows * (h + lab)), 'white'); d = ImageDraw.Draw(S)
    f = ImageFont.truetype(F, 17); f2 = ImageFont.truetype(F, 15)
    for k, (tag, r) in enumerate(items):
        x = (k % cols) * w; y = (k // cols) * (h + lab)
        im = Image.open(thumb(a.out, r['id'])).convert('RGB')
        W, H = im.size; th = int(W * 9 / 16); t = (H - th) // 2
        S.paste(im.crop((0, t, W, t + th)).resize((w - 6, h - 6)), (x + 3, y + 3))
        d.text((x + 6, y + h + 2), f"{tag} {r['views']:,}回 {int(r['dur']) // 60}分", font=f, fill='black')
        d.text((x + 6, y + h + 24), (r['ch'] or '')[:34], font=f2, fill='#444')
    p = os.path.join(a.out, f'sheet_{a.name}.jpg'); S.save(p, quality=85); print('wrote', p)


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest='cmd', required=True)
    s = sp.add_parser('search'); s.add_argument('--out', required=True); s.add_argument('--n', type=int, default=40); s.add_argument('queries', nargs='+')
    s = sp.add_parser('detail'); s.add_argument('--out', required=True); s.add_argument('--top', type=int, default=150)
    s = sp.add_parser('channels'); s.add_argument('--out', required=True); s.add_argument('--top', type=int, default=60)
    s = sp.add_parser('sheet'); s.add_argument('--out', required=True); s.add_argument('--query', required=True); s.add_argument('--name', required=True)
    a = ap.parse_args()
    dict(search=cmd_search, detail=cmd_detail, channels=cmd_channels, sheet=cmd_sheet)[a.cmd](a)


if __name__ == '__main__':
    main()
