"""肩書き・チャンネル名の型・用途の表示と再生の関係（consult-05-brand-data.md 用、2026-10-23）。

リポジトリの直下で実行する（先に classify_channels.py で brand_channels_2026-10-23.csv を作っておく）:
    python3 tools/analysis/brand/brand_analysis.py
依存: pandas, numpy, statsmodels
出力: docs/research/data/brand_*.csv と、画面への要約
"""
import re, os, json
import numpy as np, pandas as pd, warnings
warnings.filterwarnings('ignore')
import statsmodels.formula.api as smf

D = 'docs/research/data/'
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 300); pd.set_option('display.max_colwidth', 70)

# ---- 題名・チャンネル名の手がかり ----
VOICE = r'アナウンサー|NHK|ＮＨＫ|放送局|局アナ|テレビ番組MC|ナレーター|声優|俳優|女優|役者|朗読家|語り部|落語家|パーソナリティー|キャスター'
ORG = r'劇団|公式|Official|協会|(?<!猫の)事務所|学苑|NPO|一般社団法人|演劇|シアターユニット|SPAC|ハミングプロ|朗読集団|声優集団|朗読[^」』]{0,6}教室'
KNOWN = r'窪田等|魚住りえ|近藤サト|中江有里|進藤晶子|中島歩|平野啓子|日髙徹郎|日高徹郎|西村俊彦|江守徹|宮沢りえ|中嶋朋子|市原悦子|沢城みゆき|渡辺謙|橋爪|壤晴彦|国井雅比古|國井雅比古|浅沼晋太郎|阿座上洋平|岸田今日子|森本レオ|長岡輝子|寺田農|仲代|鳥海浩輔|下野紘|中尾隆聖|井上和彦|竹内由恵|田中瞳|大熊英司|白鳥怜奈|にじさんじ|ホロライブ|hololive'
SLEEP = r'睡眠|寝落ち|眠れ|眠く|眠り|おやすみ|お休み|入眠|安眠|寝かしつけ|寝る前|ねむ'
WORK = r'作業用|作業時間|BGM|勉強用|勉強|聞き流し|ながら'
COLL = r'集|選|まとめ|作品|篇|編|全\d+|\d+話|\d+作|メドレー|詰め合わせ|一挙|連続'

v = pd.read_csv(D + 'growth_videos_64works_2026-10-23.csv')
v = v[v.is_rodoku & ~v.live].copy()
ch = pd.read_csv(D + 'brand_channels_2026-10-23.csv')
v = v.merge(ch[['chid', 'name_type', 'f_auth_voice', 'f_auth_org', 'f_use', 'f_person', 'f_mood', 'f_hint', 'desc_auth_voice', 'n_videos', 'years']],
            left_on='channel_id', right_on='chid', how='left')
v['title'] = v.title.fillna(''); v['channel'] = v.channel.fillna('')
v['subs'] = v.channel_subscribers
v = v[v.subs.notna() & (v.subs > 0) & v.minutes.notna()].copy()
v['lv'] = np.log10(v.views + 1)
v['ls'] = np.log10(v.subs + 10)
v['age'] = v.age_days_approx.clip(lower=7)
v['la'] = np.log10(v.age)
v['dur'] = pd.cut(v.minutes, [0, 5, 15, 30, 60, 120, 1e5], labels=['a<5', 'b5-15', 'c15-30', 'd30-60', 'e60-120', 'f120+'], right=False).astype(str)
v['t_voice'] = v.title.str.contains(VOICE)
v['c_voice'] = v.channel.str.contains(VOICE)
v['t_org'] = v.title.str.contains(ORG)
v['c_org'] = v.channel.str.contains(ORG)
v['cue_voice'] = v.t_voice | v.c_voice
v['cue_org'] = (v.t_org | v.c_org) & ~v.cue_voice
v['cue'] = v.cue_voice | v.t_org | v.c_org
v['known'] = v.title.str.contains(KNOWN) | v.channel.str.contains(KNOWN) | (v.subs >= 100000)
# 説明欄だけで職業を書いている（題名とチャンネル名には出していない）
v['desc_only'] = v.desc_auth_voice.fillna(False).astype(bool) & ~v.cue
v['sleep'] = v.title.str.contains(SLEEP)
v['workw'] = v.title.str.contains(WORK)
v['use'] = v.sleep | v.workw
v['coll'] = v.title.str.contains(COLL)
v['recent'] = v.age <= 3 * 365
for c in ['cue', 'cue_voice', 'cue_org', 't_voice', 'c_voice', 'known', 'desc_only', 'sleep', 'workw', 'use', 'coll']:
    v[c] = v[c].astype(int)

BASE = 'lv ~ ls + la + C(work) + C(dur)'


def fit(df, terms, base=BASE):
    f = base + ' + ' + ' + '.join(terms)
    m = smf.ols(f, data=df).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(df.channel_id)[0]})
    out = []
    for t in terms:
        b, se = m.params[t], m.bse[t]
        sub = df[df[t] == 1]
        out.append(dict(term=t, n=len(df), n_with=int(df[t].sum()), ch_with=int(sub.channel_id.nunique()),
                        ratio=round(10 ** b, 2), lo=round(10 ** (b - 1.96 * se), 2), hi=round(10 ** (b + 1.96 * se), 2),
                        p=round(m.pvalues[t], 3)))
    return out


SAMPLES = {
    '全体': v,
    '登録者10万人未満': v[v.subs < 100000],
    '登録者1万人未満': v[v.subs < 10000],
    '登録者1万人未満・投稿3年以内': v[(v.subs < 10000) & v.recent.astype(bool)],
}
res = []
print('==== 問1 肩書きの手がかり（題名かチャンネル名）')
for name, df in SAMPLES.items():
    for excl in [False, True]:
        d = df[df.known == 0] if excl else df
        for terms in (['cue'], ['cue_voice', 'cue_org'], ['t_voice', 'c_voice']):
            for r in fit(d, terms):
                r.update(sample=name, known_excluded=excl); res.append(r)
# 説明欄だけで職業を書くチャンネル（名乗り方の違い）
for name in ['登録者1万人未満', '登録者10万人未満']:
    d = SAMPLES[name]; d = d[d.known == 0]
    for r in fit(d, ['cue_voice', 'desc_only']):
        r.update(sample=name, known_excluded=True, note='説明欄だけ'); res.append(r)
R1 = pd.DataFrame(res)
R1.to_csv(D + 'brand_q1_authority_2026-10-23.csv', index=False)
print(R1.to_string())

# 肩書きのある小さなチャンネルの動画（目で確かめる用）
sm = v[(v.subs < 10000) & (v.cue == 1)].sort_values('views', ascending=False)
sm[['work', 'title', 'channel', 'subs', 'views', 'minutes', 'age', 'known']].to_csv(D + 'brand_q1_small_cue_videos_2026-10-23.csv', index=False)
print(sm[['title', 'channel', 'subs', 'views', 'minutes', 'age', 'known']].head(40).to_string())
print('小さなチャンネル 肩書きあり 動画', len(sm), 'チャンネル', sm.channel_id.nunique(), ' 知名度ありを除く', (sm.known == 0).sum(), sm[sm.known == 0].channel_id.nunique())
print(sm.groupby('channel').agg(n=('views', 'size'), subs=('subs', 'first'), med=('views', 'median')).sort_values('n', ascending=False).to_string())

# 題名の肩書き（1万人未満・3年以内）：チャンネルを1つずつ抜いたときの倍率の幅
d = SAMPLES['登録者1万人未満・投稿3年以内']; d = d[d.known == 0]
jk = []
for cid in d[d.t_voice == 1].channel_id.unique():
    jk.append((fit(d[d.channel_id != cid], ['t_voice'])[0]['ratio'], d[d.channel_id == cid].channel.iloc[0]))
jk.sort()
print('jackknife t_voice', jk[0], jk[-1])
pd.DataFrame(jk, columns=['ratio_without', 'channel_left_out']).to_csv(D + 'brand_q1_jackknife_2026-10-23.csv', index=False)
print(d[d.t_voice == 1].groupby('channel').agg(n=('views', 'size'), subs=('subs', 'first'), med=('views', 'median'), mn=('minutes', 'median')).sort_values('med', ascending=False).to_string())

# 単純な比較（中央値・1,000回以上の割合）
def simple(df, col):
    g = df.groupby(col).agg(n=('views', 'size'), ch=('channel_id', 'nunique'), med=('views', 'median'), p1k=('views', lambda x: (x >= 1000).mean()), min_med=('minutes', 'median'), subs_med=('subs', 'median'))
    return g.round(2)
# 仄めかし（声・ナレーションを連想させるチャンネル名）の動画
hv = v[v.f_hint.fillna(False).astype(bool)]
print('仄めかしのチャンネル名の動画', len(hv), hv.channel_id.nunique(), hv.views.median())
print(hv.groupby('channel').agg(n=('views', 'size'), subs=('subs', 'first'), med=('views', 'median')).to_string())
print('---- 単純比較 1万人未満・3年以内・知名度なし')
d = SAMPLES['登録者1万人未満・投稿3年以内']; d = d[d.known == 0]
print(simple(d, 'cue'))

# ---- 問2 チャンネル名の型 ----
print('==== 問2 チャンネル名の型')
c = ch[(ch.rod_share >= 0.5) & ch.subs.notna() & (ch.n_videos > 0)].copy()
c['young'] = c.years <= 3


def chsumm(x):
    return pd.Series(dict(n=len(x), subs_med=x.subs.median(), p1k=(x.subs >= 1000).mean(), p10k=(x.subs >= 10000).mean(),
                          nvid_med=x.n_videos.median(), years_med=x.years.median(), spv_med=(x.subs / x.n_videos).median(),
                          r3_ch=int(x.recent3y_med_views.notna().sum()), r3_views_med=x.recent3y_med_views.median(), r3_vpd_med=x.recent3y_med_vpd.median()))
T2 = c.groupby('name_type').apply(chsumm).round(2)
T2y = c[c.young].groupby('name_type').apply(chsumm).round(2)
print(T2.to_string()); print('開設3年以内'); print(T2y.to_string())
# 本数・年数をそろえた登録者の差（c 個人名を基準）。知名度のある人を含む場合と除く場合
def typereg(df, f):
    m = smf.ols(f + ' + C(name_type, Treatment("c_個人名"))', data=df).fit(cov_type='HC1')
    out = []
    for k in m.params.index:
        if k.startswith('C(name_type'):
            b, se = m.params[k], m.bse[k]; t = k.split('[T.')[1][:-1]
            out.append(dict(type=t, n_type=int((df.name_type == t).sum()), n=len(df), ratio=round(10 ** b, 2), lo=round(10 ** (b - 1.96 * se), 2), hi=round(10 ** (b + 1.96 * se), 2), p=round(m.pvalues[k], 3)))
    return out
cc = c[(c.subs > 0) & c.years.notna()].copy()
cc['lsub'] = np.log10(cc.subs); cc['lnv'] = np.log10(cc.n_videos); cc['ly'] = np.log10(cc.years.clip(lower=0.25))
cc = cc[cc.recent3y_med_vpd.isna() | (cc.recent3y_med_vpd >= 0)]
cc['lvpd'] = np.log10(cc.recent3y_med_vpd.clip(lower=0.01))
reg = []
for excl in [False, True]:
    d = cc[~cc.known] if excl else cc
    for r in typereg(d, 'lsub ~ lnv + ly'):
        r.update(model='登録者~本数+年数', known_excluded=excl); reg.append(r)
    d3 = d[d.recent3y_med_vpd.notna()]
    for r in typereg(d3, 'lvpd ~ lsub'):
        r.update(model='直近3年の1日あたり再生~登録者', known_excluded=excl); reg.append(r)
REG2 = pd.DataFrame(reg)
print(REG2.to_string())
REG2.to_csv(D + 'brand_q2_name_type_reg_2026-10-23.csv', index=False)
print('知名度ありのチャンネル', cc[cc.known].groupby('name_type').size().to_dict())
# フラグ（重なりを許す）ごと
fl = []
for f in ['f_use', 'f_mood', 'f_person', 'f_auth_voice', 'f_auth_org', 'f_hint']:
    for val in [True, False]:
        x = c[c[f] == val]
        s = chsumm(x); s['flag'] = f; s['value'] = val; fl.append(s)
FL = pd.DataFrame(fl).round(2)
print(FL.to_string())
out2 = pd.concat([T2.assign(scope='全体'), T2y.assign(scope='開設3年以内')])
out2.to_csv(D + 'brand_q2_name_type_2026-10-23.csv')
# 動画単位：チャンネル名の型ごとの再生（登録者・作品・長さ・年数をそろえる）
vv = v[v.name_type.notna()].copy()
for name, df in [('全体', vv), ('登録者1万人未満', vv[vv.subs < 10000]), ('登録者1万人未満・投稿3年以内', vv[(vv.subs < 10000) & (vv.recent == 1)])]:
    m4 = smf.ols(BASE + ' + C(name_type, Treatment("c_個人名"))', data=df).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(df.channel_id)[0]})
    print('動画単位', name, len(df))
    for k in m4.params.index:
        if k.startswith('C(name_type'):
            b, se = m4.params[k], m4.bse[k]
            print('  ', k.split('[T.')[1][:-1], int((df.name_type == k.split('[T.')[1][:-1]).sum()), round(10 ** b, 2), round(10 ** (b - 1.96 * se), 2), round(10 ** (b + 1.96 * se), 2), round(m4.pvalues[k], 3))
    print('  基準 c_個人名', int((df.name_type == 'c_個人名').sum()))

# ---- 問3 用途を出した題名：長い版に限る ----
print('==== 問3 用途の言葉（題名）')
res3 = []
for name, df in [('全体', v), ('30分以上', v[v.minutes >= 30]), ('60分以上', v[v.minutes >= 60]), ('60分以上・登録者10万人未満', v[(v.minutes >= 60) & (v.subs < 100000)]),
                 ('60分以上・登録者1万人未満', v[(v.minutes >= 60) & (v.subs < 10000)]), ('60分以上・投稿3年以内', v[(v.minutes >= 60) & (v.recent == 1)]),
                 ('30分以上・複数作品', v[(v.minutes >= 30) & (v.coll == 1)]), ('30分未満', v[v.minutes < 30])]:
    for terms in (['use'], ['sleep'], ['workw']):
        try:
            for r in fit(df, terms):
                r.update(sample=name); res3.append(r)
        except Exception as e:
            print('err', name, terms, e)
R3 = pd.DataFrame(res3)
R3.to_csv(D + 'brand_q3_use_words_2026-10-23.csv', index=False)
print(R3.to_string())
d = v[v.minutes >= 60]
print(d.groupby('use').agg(n=('views', 'size'), ch=('channel_id', 'nunique'), med=('views', 'median'), subs_med=('subs', 'median'), min_med=('minutes', 'median')).to_string())
# 用途の言葉と肩書きの重なり（題名）
print(pd.crosstab(v.use, v.cue, margins=True))
