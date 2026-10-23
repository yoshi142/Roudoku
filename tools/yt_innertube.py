#!/usr/bin/env python3
"""YouTube の内部 API（youtubei/v1/next）から、動画の投稿日・登録者数・上位コメントを取る。

yt-dlp の動画ページ取得が回数制限（bot 確認）で止まったときの代わりに使う。外部ライブラリ不要（curl を使う）。
使い方:
  python3 tools/yt_innertube.py VIDEO_ID [--comments 20]
  python3 tools/yt_innertube.py --batch ids.txt --out details.jsonl --comments 20 --sleep 1.5
出力（1行1動画の JSON）: id, date_text, upload_date（YYYY-MM-DD に直せたもの）, views_text, subs_text, subs（数値に直したもの）, comments[{text, likes}]
注意: 非公式の窓口なので、仕様が変わると動かなくなる。間隔を空けて使う。
"""
import argparse, json, re, subprocess, sys, time

CLIENT = {"clientName": "WEB", "clientVersion": "2.20261020.00.00", "hl": "ja", "gl": "JP"}


def post(body):
    body = {"context": {"client": CLIENT}, **body}
    r = subprocess.run(['curl', '-sS', '--max-time', '40', '-X', 'POST', '-H', 'Content-Type: application/json',
                        '-H', 'Accept-Language: ja', 'https://www.youtube.com/youtubei/v1/next?prettyPrint=false',
                        '--data', json.dumps(body)], capture_output=True)
    try:
        return json.loads(r.stdout)
    except Exception:
        return {'_error': r.stdout[:200].decode('utf-8', 'replace')}


def walk(o, key):
    if isinstance(o, dict):
        for k, v in o.items():
            if k == key:
                yield v
            yield from walk(v, key)
    elif isinstance(o, list):
        for v in o:
            yield from walk(v, key)


def text_of(x):
    if not x:
        return ''
    if 'simpleText' in x:
        return x['simpleText']
    return ''.join(r.get('text', '') for r in x.get('runs', []))


def ja_number(s):
    """「チャンネル登録者数 1.2万人」「30万」「1,234」→ 数値"""
    m = re.search(r'([0-9][0-9.,]*)\s*(万|億)?', s or '')
    if not m:
        return None
    v = float(m.group(1).replace(',', ''))
    return int(v * {'万': 1e4, '億': 1e8}.get(m.group(2), 1))


def to_date(s):
    m = re.search(r'(\d{4})/(\d{1,2})/(\d{1,2})', s or '')
    return f'{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}' if m else None


def video(vid, ncomments=20):
    d = post({"videoId": vid})
    if '_error' in d:
        return {'id': vid, 'error': d['_error']}
    pri = next(walk(d, 'videoPrimaryInfoRenderer'), {})
    own = next(walk(d, 'videoOwnerRenderer'), {})
    date_text = text_of(pri.get('dateText'))
    res = dict(id=vid, date_text=date_text, upload_date=to_date(date_text),
               views_text=text_of(next(walk(pri, 'viewCount'), {}).get('videoViewCountRenderer', {}).get('viewCount')) if pri else '',
               subs_text=text_of(own.get('subscriberCountText')), comments=[])
    res['subs'] = ja_number(res['subs_text'])
    if ncomments <= 0:
        return res
    tok = None
    for sec in walk(d, 'itemSectionRenderer'):
        if sec.get('sectionIdentifier') == 'comment-item-section':
            tok = next((c.get('token') for c in walk(sec, 'continuationCommand')), None)
    pages = 0
    while tok and len(res['comments']) < ncomments and pages < 4:
        e = post({"continuation": tok}); pages += 1
        for p in walk(e, 'commentEntityPayload'):
            props = p.get('properties', {})
            tb = p.get('toolbar', {})
            res['comments'].append(dict(text=props.get('content', {}).get('content', ''),
                                        likes=ja_number(tb.get('likeCountNotliked', '')) or 0,
                                        reply_count=ja_number(tb.get('replyCount', '')) or 0))
        tok = None
        for c in walk(e.get('onResponseReceivedEndpoints', []), 'continuationCommand'):
            tok = c.get('token')
        time.sleep(0.8)
    res['comments'] = res['comments'][:ncomments]
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('vid', nargs='?')
    ap.add_argument('--batch'); ap.add_argument('--out')
    ap.add_argument('--comments', type=int, default=20)
    ap.add_argument('--sleep', type=float, default=1.5)
    a = ap.parse_args()
    if a.vid:
        print(json.dumps(video(a.vid, a.comments), ensure_ascii=False, indent=1)); return
    done = set()
    try:
        for l in open(a.out, encoding='utf-8'):
            j = json.loads(l)
            if not j.get('error'):
                done.add(j['id'])
    except FileNotFoundError:
        pass
    with open(a.out, 'a', encoding='utf-8') as f:
        for line in open(a.batch, encoding='utf-8'):
            p = line.split()
            if not p or p[0] in done:
                continue
            n = int(p[1]) if len(p) > 1 else a.comments
            r = video(p[0], n)
            f.write(json.dumps(r, ensure_ascii=False) + '\n'); f.flush()
            print(p[0], r.get('upload_date'), r.get('subs'), len(r.get('comments', [])), r.get('error', '')[:60], flush=True)
            time.sleep(a.sleep)


if __name__ == '__main__':
    main()
