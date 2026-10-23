import json, re, math, statistics as st, collections, csv, os, datetime
import numpy as np
import statsmodels.formula.api as smf
import pandas as pd

V = json.load(open('videos_prep.json', encoding='utf-8'))
det = {}
for l in open('details.jsonl', encoding='utf-8'):
    j = json.loads(l)
    if not j.get('error'):
        det[j['id']] = j
chs = json.load(open('chsubs_merged.json', encoding='utf-8'))
th = json.load(open('thfeat.json'))
wiki = json.load(open('wiki.json', encoding='utf-8'))
TODAY = datetime.date(2026, 10, 23)

rows = []
for r in V:
    if r['kind'] != 'narration':
        continue
    subs = chs.get(r['chid'])
    if subs is None and r['id'] in det:
        subs = det[r['id']].get('subs')
    d = dict(work=r['work'], id=r['id'], views=r['views'], min=r['min'] or 0, subs=subs, title=r['title'], ch=r['ch'], rel=r['rel'])
    for k, v in r['f'].items():
        d['f_' + k] = int(v)
    t = th.get(r['id'])
    if t:
        for k, v in t.items():
            d['t_' + k] = v
    if r['id'] in det and det[r['id']].get('upload_date'):
        up = datetime.date.fromisoformat(det[r['id']]['upload_date'])
        d['days'] = max((TODAY - up).days, 1); d['vpd'] = r['views'] / d['days']; d['year'] = up.year
    rows.append(d)
df = pd.DataFrame(rows)
df = df[df['subs'].notna() & (df['subs'] > 0)].copy()
df['lv'] = np.log10(df['views'] + 1)
df['ls'] = np.log10(df['subs'] + 10)
bins = [0, 5, 15, 30, 60, 120, 1e9]
labs = ['a_5分未満', 'b_5-15分', 'c_15-30分', 'd_30-60分', 'e_1-2時間', 'f_2時間以上']
df['dur'] = pd.cut(df['min'], bins=bins, labels=labs, right=False)
ren = {c: 'x%d' % i for i, c in enumerate([c for c in df.columns if c.startswith('f_')])}
inv = {v: k[2:] for k, v in ren.items()}
df = df.rename(columns=ren)
out = {'n': len(df)}

# 1) 登録者数と作品をそろえた回帰
fx = ' + '.join(ren.values())
m = smf.ols(f'lv ~ ls + C(work) + C(dur, Treatment("b_5-15分")) + {fx}', data=df).fit(cov_type='HC1')
res = []
for k, v in m.params.items():
    if k.startswith('x') or k.startswith('C(dur') or k == 'ls':
        name = inv.get(k, k)
        res.append((name, v, m.bse[k], m.pvalues[k]))
out['reg_title_dur'] = [(a, round(10 ** b, 2), round(c, 3), round(p, 4)) for a, b, c, p in res]
out['reg_r2'] = round(m.rsquared, 3)

# 2) サムネイルの数値（標準化して投入）
tcols = [c for c in df.columns if c.startswith('t_')]
d2 = df.dropna(subset=tcols).copy()
for c in tcols:
    d2[c + '_z'] = (d2[c] - d2[c].mean()) / d2[c].std()
m2 = smf.ols('lv ~ ls + C(work) + ' + ' + '.join(c + '_z' for c in tcols), data=d2).fit(cov_type='HC1')
out['reg_thumb'] = [(k, round(10 ** v, 2), round(m2.pvalues[k], 4)) for k, v in m2.params.items() if k.endswith('_z')]

# 3) 長さ別（登録者1万人未満のチャンネルに限る：小さなチャンネルで何が伸びるか）
small = df[df['subs'] < 10000]
out['small_by_dur'] = []
for lab in labs:
    g = small[small['dur'] == lab]
    if len(g):
        out['small_by_dur'].append((lab, len(g), round(float(g['rel'].median()), 2), int(g['views'].median()), int((g['views'] >= 10000).sum())))
# 4) 年と1日あたり再生
g = df.dropna(subset=['vpd'])
out['vpd_by_dur'] = [(lab, int(len(g[g['dur'] == lab])), round(float(g[g['dur'] == lab]['vpd'].median()), 1)) for lab in labs if len(g[g['dur'] == lab])]
out['recent_top'] = g[g['year'] >= 2025].sort_values('vpd', ascending=False).head(25)[['work', 'title', 'ch', 'subs', 'views', 'vpd', 'min']].to_dict('records')
out['small_winners'] = df[(df['subs'] < 20000) & (df['views'] >= 20000)].sort_values('views', ascending=False).head(30)[['work', 'title', 'ch', 'subs', 'views', 'min', 'id']].to_dict('records')
json.dump(out, open('analysis_out.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
df.to_csv('analysis_df.csv', index=False)
print(json.dumps({k: out[k] for k in ['n', 'reg_r2', 'reg_title_dur', 'reg_thumb', 'small_by_dur', 'vpd_by_dur']}, ensure_ascii=False, indent=1))
