import json, subprocess, re, time, sys
CLIENT = {"clientName": "WEB", "clientVersion": "2.20261020.00.00", "hl": "ja", "gl": "JP"}
def post(ep, body):
    body = {"context": {"client": CLIENT}, **body}
    r = subprocess.run(['curl','-sS','--max-time','40','-X','POST','-H','Content-Type: application/json','-H','Accept-Language: ja',
        f'https://www.youtube.com/youtubei/v1/{ep}?prettyPrint=false','--data',json.dumps(body)],capture_output=True)
    try: return json.loads(r.stdout)
    except Exception: return {'_error': r.stdout[:300].decode('utf-8','replace')}
def walk(o, key):
    if isinstance(o, dict):
        for k, v in o.items():
            if k == key: yield v
            yield from walk(v, key)
    elif isinstance(o, list):
        for v in o: yield from walk(v, key)
def text_of(x):
    if not x: return ''
    if 'simpleText' in x: return x['simpleText']
    return ''.join(r.get('text','') for r in x.get('runs',[]))
def num(s):
    m = re.search(r'([0-9][0-9.,]*)\s*(万|億)?', s or '')
    if not m: return None
    return int(float(m.group(1).replace(',',''))*{'万':1e4,'億':1e8}.get(m.group(2),1))
def ago_days(s):
    # "3 年前" "2か月前" "5 日前" "1 週間前" "配信済み: 3 年前"
    m = re.search(r'(\d+)\s*(秒|分|時間|日|週間|か月|ヶ月|年)前', s or '')
    if not m: return None
    n=int(m.group(1)); u=m.group(2)
    return n*{'秒':0,'分':0,'時間':0,'日':1,'週間':7,'か月':30.4,'ヶ月':30.4,'年':365.25}[u]
def dur(s):
    if not s: return None
    p=[int(x) for x in s.split(':')]; t=0
    for x in p: t=t*60+x
    return t
