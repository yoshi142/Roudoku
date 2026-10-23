import json,subprocess,sys,time,re
sys.path.insert(0,'/home/user/Roudoku/tools')
from yt_innertube import walk, ja_number, CLIENT
def browse(cid):
    body={"context":{"client":CLIENT},"browseId":cid}
    r=subprocess.run(['curl','-sS','--max-time','40','-X','POST','-H','Content-Type: application/json','https://www.youtube.com/youtubei/v1/browse?prettyPrint=false','--data',json.dumps(body)],capture_output=True)
    try: return json.loads(r.stdout)
    except Exception: return None
V=json.load(open('videos_prep.json',encoding='utf-8'))
ids=[]; 
for r in V:
    if r['chid'] and r['chid'] not in ids: ids.append(r['chid'])
out={}
try: out=json.load(open('chsubs_it.json',encoding='utf-8'))
except Exception: pass
for i,cid in enumerate(ids):
    if cid in out: continue
    d=browse(cid)
    subs=None
    if d:
        s=json.dumps(d,ensure_ascii=False)
        m=re.search(r'"metadataParts": \[\{"text": \{"content": "チャンネル登録者数 ([0-9.,]+\s*(?:万|億)?)人"',s)
        if m: subs=ja_number(m.group(1))
        else:
            m=re.search(r'"metadataParts": \[\{"text": \{"content": "[^"]*"[^\]]*?\{"text": \{"content": "チャンネル登録者数 ([0-9.,]+\s*(?:万|億)?)人"',s)
            if m: subs=ja_number(m.group(1))
            elif re.search(r'本の動画',s): subs=0
    out[cid]=subs
    if i%25==0:
        json.dump(out,open('chsubs_it.json','w',encoding='utf-8')); print(i,cid,subs,flush=True)
    time.sleep(1.0)
json.dump(out,open('chsubs_it.json','w',encoding='utf-8')); print('done',len(out))
