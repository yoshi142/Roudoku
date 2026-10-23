import json, sys, time
from it import *
def parse(d):
    out=[]
    for lv in walk(d, 'lockupViewModel'):
        m = lv.get('metadata', {}).get('lockupMetadataViewModel', {})
        parts = [p.get('text', {}).get('content', '') for row in walk(m, 'metadataRows') for r in row for p in r.get('metadataParts', [])]
        badge = next((b.get('text') for b in walk(lv.get('contentImage', {}), 'thumbnailBadgeViewModel')), None)
        out.append(dict(id=lv.get('contentId'), title=m.get('title', {}).get('content'), views=num(parts[0]) if parts else None,
                        age=ago_days(parts[1]) if len(parts) > 1 else None, sec=dur(badge) if badge and ':' in badge else None))
    return out
def all_videos(cid, maxpages=40):
    d = post('browse', {"browseId": cid, "params": "EgZ2aWRlb3PyBgQKAjoA"})
    vids = parse(d); pages=1
    def grid_tok(x):
        toks=[c['token'] for c in walk(x,'continuationCommand') if c.get('request')=='CONTINUATION_REQUEST_TYPE_BROWSE']
        return toks
    # the rich grid continuation is inside continuationItemRenderer
    def next_tok(x):
        for ci in walk(x,'continuationItemRenderer'):
            t=next(walk(ci,'continuationCommand'),{}).get('token')
            if t: return t
    tok = next_tok(d)
    while tok and pages < maxpages:
        time.sleep(0.8)
        e = post('browse', {"continuation": tok}); pages+=1
        vids += parse(e); tok = next_tok(e)
    return vids, bool(tok)
if __name__=='__main__':
    out=sys.argv[1]
    with open(out,'a',encoding='utf-8') as f:
        for cid in sys.argv[2:]:
            v,more=all_videos(cid)
            f.write(json.dumps(dict(chid=cid,videos=v,truncated=more),ensure_ascii=False)+'\n'); f.flush()
            print(cid,len(v),more,flush=True)
