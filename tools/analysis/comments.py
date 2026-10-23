import json, re, collections
CAT = [
    ('眠り・寝落ち', r'眠|寝|ねむ|おやすみ|睡眠|不眠|寝落ち|入眠'),
    ('教科書・学校の記憶', r'教科書|授業|国語|小学|中学|高校|習った|学校|音読|テスト|読書感想文|教材|宿題|夏休み|意見文|放送部|受験|古典の時間'),
    ('懐かしさ・子どもの頃', r'懐かし|なつかし|子供の頃|子どもの頃|幼い頃|小さい頃|昔読|昔聞|昔習'),
    ('声・読み方への評価', r'声|読み方|語り|朗読が|間の取り|聴きやすい|聞きやすい|滑舌|抑揚|演じ分け|上手|素晴らしい朗読|朗読して|読んで(くださ|頂|いただ)'),
    ('作品の感想・解釈', r'話|物語|結末|ラスト|主人公|作品|描写|意味|教訓|文章|名作|考えさせ|情景|カンダタ|犍陀多|メロス|ごん|蟹|クラムボン|下人|先生とK|李徴'),
    ('感動・涙', r'泣|涙|感動|胸が|切な|せつな|号泣|沁み|しみる|染み'),
    ('感謝', r'ありがとう|感謝|ありがたい|有難'),
    ('リクエスト・次回への期待', r'リクエスト|読んでほしい|読んで欲しい|希望|次は|他の作品|聴きたい|聞きたい|続き|お願いします'),
    ('子どもと聞く・読み聞かせ', r'子供と|子どもと|息子|娘|孫|読み聞かせ|うちの子|我が子'),
    ('作業・移動中', r'作業中|作業用|作業しながら|運転|通勤|家事|仕事中|勉強中|聞きながら|聴きながら|ドライブ'),
    ('いまの自分と重ねる（大人になって）', r'大人になって|大人になった|今になって|今読む|この年|歳になって|年齢|改めて|今更'),
    ('外国語・日本語学習', r'外国人|日本語の勉強|日本語を勉強|日本語学習|learning|Japanese|japanese'),
]
D = [json.loads(l) for l in open('details.jsonl', encoding='utf-8')]
D = [d for d in D if d.get('comments')]
V = {r['id']: r for r in json.load(open('videos_prep.json', encoding='utf-8'))}
allc = []
for d in D:
    v = V.get(d['id'], {})
    if v.get('kind') != 'narration':
        continue
    for c in d['comments']:
        allc.append(dict(vid=d['id'], work=v.get('work'), min=v.get('min') or 0, kind=v.get('kind'), text=c['text'], likes=c.get('likes') or 0))
print('動画', len(D), 'コメント', len(allc))
cnt = collections.Counter(); lk = collections.Counter(); tot_l = sum(c['likes'] for c in allc) or 1
by_len = {'short': collections.Counter(), 'long': collections.Counter()}; n_len = collections.Counter()
for c in allc:
    hit = [name for name, p in CAT if re.search(p, c['text'])]
    c['cats'] = hit
    for h in hit:
        cnt[h] += 1; lk[h] += c['likes']
    key = 'long' if c['min'] >= 60 else 'short'
    n_len[key] += 1
    for h in hit:
        by_len[key][h] += 1
print('\n分類（1つのコメントが複数に入ることがある）')
for name, _ in CAT:
    print(f"{name:<22} {cnt[name]:4}件 {cnt[name] / len(allc) * 100:5.1f}%  いいね比 {lk[name] / tot_l * 100:5.1f}%  | 1時間未満 {by_len['short'][name] / max(n_len['short'], 1) * 100:5.1f}%  1時間以上 {by_len['long'][name] / max(n_len['long'], 1) * 100:5.1f}%")
print('n_len', dict(n_len))
json.dump(allc, open('comments_all.json', 'w', encoding='utf-8'), ensure_ascii=False)
# いいねの多いコメント（分類ごと上位3件）
print('\n代表例')
for name, _ in CAT:
    top = sorted([c for c in allc if name in c['cats']], key=lambda c: -c['likes'])[:3]
    for c in top:
        print(f"[{name}] ({c['work']}, いいね{c['likes']}) {c['text'][:110].replace(chr(10), ' ')}")
