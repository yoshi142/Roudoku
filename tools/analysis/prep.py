import json,re,collections,statistics as st,math
rows=[json.loads(l) for l in open('search.jsonl',encoding='utf-8')]
VAR={'ごんぎつね':['ごんぎつね','ごん狐','ごんぎつね'],'汚れつちまつた悲しみに':['汚れつちまつた','汚れっちまった','汚れちまった'],'こころ':['こころ','こゝろ'],'坊っちゃん':['坊っちゃん','坊ちゃん','坊つちやん'],'手袋を買いに':['手袋を買いに','手ぶくろを買いに','てぶくろをかいに'],'おくのほそ道':['おくのほそ道','奥の細道','奥のほそ道'],'吾輩は猫である':['吾輩は猫である','我輩は猫である'],'智恵子抄':['智恵子抄','レモン哀歌','あどけない話'],'耳なし芳一':['耳なし芳一','耳無し芳一','耳無芳一'],'雨ニモマケズ':['雨ニモマケズ','雨にも負けず'],'檸檬':['檸檬','レモン'],'形':['「形」','『形』','形 菊池','菊池寛「形」','菊池寛『形』'],'鼻':['「鼻」','『鼻』','鼻 芥川','芥川龍之介「鼻」','鼻／','鼻・']}
def relevant(r):
    t=r['title'] or ''
    vs=VAR.get(r['work'],[r['work']])
    return any(v in t for v in vs)
def kind(t):
    if re.search(r'絵本|アニメ|動く|紙芝居|えほん|Web絵本|ペープサート',t): return 'picture'
    if re.search(r'解説|要約|あらすじ|考察|授業|テスト|読書感想文|徹底|入試|分かる|わかる|名著|YouTube大学|学ぶ|講義|まとめて解説|ゆっくり解説',t): return 'explain'
    if re.search(r'歌|うた|ソング|合唱|Song|song|弾き語り|MV',t) and not re.search(r'朗読',t): return 'song'
    return 'narration'
F={
 '【朗読】の印':r'【朗読】|\[朗読\]|【名作朗読】|【古典朗読】',
 '睡眠・寝落ち':r'睡眠|寝落ち|眠れる|眠くなる|おやすみ|入眠|安眠|寝かしつけ|ねむ|眠り',
 '作業用・BGM':r'作業用|BGM|聞き流し|ながら',
 '朗読者名（朗読：〇〇など）':r'朗読[：:・]|語り[：:]|ナレーター|朗読\s*[一-龥ぁ-んァ-ヶ]{2,}$|読み手',
 '職業（アナウンサー・声優など）':r'アナウンサー|声優|俳優|ナレーター|女優',
 '『』かぎかっこ':r'『',
 '作者名':None,
 '分数・時間':r'\d+\s*分|\d+\s*時間|\d+min',
 '広告なし':r'広告なし|広告無し',
 '字幕':r'字幕',
 '教科書・学校':r'教科書|国語|授業|中学|小学|高校|教材|学年',
 '全文・完全版':r'全文|完全版|ノーカット|全編|全話',
 '複数作品（集・選・メドレー）':r'集|選|メドレー|まとめ|作品|全\d+',
 '英語の併記':r'[A-Za-z]{5,}',
}
AUTH={'芥川龍之介':'芥川','太宰治':'太宰','宮沢賢治':'賢治','新美南吉':'南吉','中島敦':'中島','夏目漱石':'漱石','森鴎外':'鴎外|鷗外','梶井基次郎':'梶井','小川未明':'未明','菊池寛':'菊池','有島武郎':'有島','島崎藤村':'藤村','中原中也':'中也','高村光太郎':'光太郎','鴨長明':'長明','清少納言':'清少納言','兼好法師':'兼好','松尾芭蕉':'芭蕉','坂口安吾':'安吾','江戸川乱歩':'乱歩','小泉八雲':'八雲'}
works={l.split('\t')[0]:l.split('\t')[1] for l in open('works.tsv',encoding='utf-8')}
V=[]
seen=set()
for r in rows:
    if not relevant(r): continue
    key=(r['work'],r['id'])
    if key in seen: continue
    seen.add(key)
    r=dict(r); r['kind']=kind(r['title']); r['min']=r['dur']/60 if r['dur'] else None
    a=works[r['work']]; ap=AUTH.get(a)
    feats={}
    for k,p in F.items():
        if k=='作者名': feats[k]=bool(ap and re.search(ap,r['title']))
        else: feats[k]=bool(re.search(p,r['title']))
    r['f']=feats; V.append(r)
# 作品内の相対再生（朗読のみの中央値で割る）
by=collections.defaultdict(list)
for r in V:
    if r['kind']=='narration': by[r['work']].append(r['views'])
med={w:st.median(v) for w,v in by.items() if v}
for r in V:
    m=med.get(r['work']); r['rel']=(r['views']/m) if m else None
json.dump(V,open('videos_prep.json','w',encoding='utf-8'),ensure_ascii=False)
print('関係ありの動画',len(V),collections.Counter(r['kind'] for r in V))
