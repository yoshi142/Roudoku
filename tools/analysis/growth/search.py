import sys, json, time
from it import *
def search(q, n=40):
    d = post('search', {"query": q}); out=[]; est=d.get('estimatedResults')
    pages=0
    while True:
        for v in walk(d, 'videoRenderer'):
            owner = v.get('ownerText',{}).get('runs',[{}])[0]
            out.append(dict(id=v.get('videoId'), title=text_of(v.get('title')), ch=owner.get('text'),
                chid=owner.get('navigationEndpoint',{}).get('browseEndpoint',{}).get('browseId'),
                views=num(text_of(v.get('viewCountText'))) or 0, sec=dur(text_of(v.get('lengthText'))),
                pub=text_of(v.get('publishedTimeText')), age_days=ago_days(text_of(v.get('publishedTimeText'))), rank=len(out)+1))
        tok = next(walk(d,'continuationCommand'),{}).get('token')
        pages+=1
        if len(out)>=n or not tok or pages>=6: break
        time.sleep(1); d = post('search', {"continuation": tok})
    return est, out[:n]
if __name__=='__main__':
    est,o=search(sys.argv[1], int(sys.argv[2]) if len(sys.argv)>2 else 40)
    print(est, len(o)); 
    for r in o[:8]: print(r)
