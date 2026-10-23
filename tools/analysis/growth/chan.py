import json, sys, time, os, re
from it import *
def channel(cid):
    d = post('browse', {"browseId": cid, "params": "EgZ2aWRlb3PyBgQKAjoA"})
    if '_error' in d: return {'chid': cid, 'error': d['_error'][:100]}
    res = {'chid': cid}
    md = d.get('metadata', {}).get('channelMetadataRenderer', {})
    res['name'] = md.get('title'); res['desc'] = (md.get('description') or '')[:600]
    vids = []
    for lv in walk(d, 'lockupViewModel'):
        m = lv.get('metadata', {}).get('lockupMetadataViewModel', {})
        parts = [p.get('text', {}).get('content', '') for row in walk(m, 'metadataRows') for r in row for p in r.get('metadataParts', [])]
        badge = next((b.get('text') for b in walk(lv.get('contentImage', {}), 'thumbnailBadgeViewModel')), None)
        vids.append(dict(id=lv.get('contentId'), title=m.get('title', {}).get('content'), views=num(parts[0]) if parts else None,
                         age=ago_days(parts[1]) if len(parts) > 1 else None, dur=dur(badge) if badge and ':' in badge else None))
    res['recent'] = vids
    toks = [c['token'] for c in walk(d, 'continuationCommand')]
    about = None
    s = json.dumps(d.get('header', {}), ensure_ascii=False)
    m = re.search(r'チャンネル登録者数 ([0-9.,]+\s*(万|億)?)人', s); res['subs_h'] = num(m.group(1)) if m else None
    m = re.search(r'([0-9,]+) 本の動画', s); res['nvid_h'] = num(m.group(1)) if m else None
    for t in (toks[-1:] + toks[:1]):
        time.sleep(0.6)
        e = post('browse', {"continuation": t})
        about = next(walk(e, 'aboutChannelViewModel'), None)
        if about: break
    if about:
        res['subs'] = num(about.get('subscriberCountText', '')) if about.get('subscriberCountText') else None
        res['subs_text'] = about.get('subscriberCountText')
        res['total_views'] = num(about.get('viewCountText', ''))
        res['n_videos'] = num(about.get('videoCountText', ''))
        jt = (about.get('joinedDateText') or {}).get('content', '')
        res['joined'] = to_date(jt) if 'to_date' in globals() else jt
        res['joined_text'] = jt; res['country'] = about.get('country')
    return res
import re
def to_date(s):
    m = re.search(r'(\d{4})/(\d{1,2})/(\d{1,2})', s or '')
    return f'{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}' if m else None
if __name__ == '__main__':
    ids = [l.strip() for l in open(sys.argv[1]) if l.strip()]
    if len(sys.argv) > 3 and sys.argv[3] == 'rev': ids = ids[::-1]
    out = sys.argv[2]; done = set()
    for f in [out, out.replace('_a', '_b'), out.replace('_b', '_a')]:
        if os.path.exists(f):
            for l in open(f, encoding='utf-8'):
                j = json.loads(l)
                if not j.get('error'): done.add(j['chid'])
    with open(out, 'a', encoding='utf-8') as f:
        import glob
        for cid in ids:
            d2 = set()
            for g in glob.glob(os.path.join(os.path.dirname(out), 'chan_*.jsonl')):
                for l in open(g, encoding='utf-8'):
                    try: d2.add(json.loads(l)['chid'])
                    except Exception: pass
            if cid in done or cid in d2: continue
            for k in range(3):
                r = channel(cid)
                if not r.get('error'): break
                print('error', cid, r['error'][:80], flush=True); time.sleep(30 * (k + 1))
            f.write(json.dumps(r, ensure_ascii=False) + '\n'); f.flush()
            print(cid, r.get('name'), r.get('subs'), r.get('n_videos'), r.get('joined'), len(r.get('recent', [])), flush=True)
            time.sleep(1.0)
