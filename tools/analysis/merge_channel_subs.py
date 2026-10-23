import json
V=json.load(open('videos_prep.json',encoding='utf-8'))
ids=set(r['chid'] for r in V if r['chid'])
a={};b={}
try: a=json.load(open('chsubs_it.json',encoding='utf-8'))
except Exception: pass
try: b=json.load(open('chsubs_rev.json',encoding='utf-8'))
except Exception: pass
m={**a,**{k:v for k,v in b.items() if v is not None or k not in a}}
print(len(ids), len(set(m)&ids))
json.dump(m,open('chsubs_merged.json','w',encoding='utf-8'))
