"""チャンネル名の型を分ける（consult-05-brand-data.md 用、2026-10-23）。

作業フォルダ（consult-02 の取得物 chan_*.jsonl がある場所）で実行する:
    python3 tools/analysis/brand/classify_channels.py <作業フォルダ> docs/research/data/brand_channels_2026-10-23.csv

分け方（優先順。上で当てはまったら下は見ない）
  d 肩書き・権威 : 名前に声の職業（アナウンサー、ナレーター、声優、俳優 など）か、所属・公式（劇団、公式、協会、事務所 など）
  a 用途        : 睡眠・眠・寝落ち・おやすみ・作業用・勉強・BGM・通勤・癒し など
  c 個人名      : 人の名前（本名・芸名・ハンドル名）が主になっている。手作業の一覧 PERSON による
  b 雰囲気・文芸 : 〇〇文庫、〇〇図書館、〇〇の夜、言の葉、〇〇堂・館・庵、カフェ・サロン など
  e その他      : 「名作朗読」「青空文庫朗読」のような説明的な名前、合成音声、雑学など
フラグ（f_*）は優先順と関係なく、当てはまるものすべてに立てる。
"""
import json, glob, os, re, sys
import numpy as np, pandas as pd

AUTH_VOICE = re.compile(r'アナウンサー|NHK|ＮＨＫ|テレビ番組MC|ナレーター|声優|俳優|女優|朗読家|語り部|落語家|パーソナリティー|キャスター')
AUTH_ORG = re.compile(r'劇団|公式|Official|協会|事務所|学苑|NPO|一般社団法人|演劇|シアターユニット|SPAC|サンミュージック|ハミングプロ|朗読集団|声優集団|大学|教室')
AUTH_OTHER = re.compile(r'脚本家|日本語教師|元銀座ママ')
USE = re.compile(r'睡眠|眠|ねむ|ネム|寝|おやすみ|安眠|熟眠|ぐっすり|うたたね|ねろ|SOINEOCHI|作業用|勉強|BGM|聞き流し|通勤|癒し|癒やし|いやし|Bedtime|Sleep', re.I)
MOOD = re.compile(r'文庫|図書館|図書室|書房|書斎|書店|本棚|本箱|ほんだな|館|堂|庵|夜|宵|月|星|森|庭|言の葉|ことのは|言ノ葉|言葉|カフェ|cafe|喫茶|サロン|ラウンジ|劇場|ライブラリー|ルーム|ROOM|部屋|室|横丁|通り|空間|アート|ノオト|こえ|こゑ|旅|散歩|日和|四季|しずく|灯|ランプ|ジュークボックス|玉手箱|アラモード|アリア|十色|新書|夜話|夜語り|聲|朗らか|ゼミ|出版|Voices|Lands|meadow|Leaves|amayadori|Timeless|ヨミカタリ|おはなし|お耳|書庫|音景|名著館|耳で|ねこや|朗読店|Night|Dream|夢|不朽|素朴|優しい|ベルエポック|春処|声で読む|育む|の世界|研究室|ふみを読む|悠々|文粋|朗読会|朗読倉庫|朗読の扉|朗読のとびら|朗読カルテット|朗読ジュークボックス|言の葉|文学堂', re.I)
# 仄めかし：職業を名乗らずに声の仕事を連想させる語
HINT = re.compile(r'ナレーション|Narration|Voice|ボイス|声の|声で|こえ|こゑ|語り(?!部)|職人|Studio|スタジオ|朗読アート', re.I)

# 人の名前が主になっているチャンネル（手作業で判定。名前の一部で照合）
PERSON = """窪田等|しまえりこ|天乃悠|西村俊彦|枡太|小梅小町|あべよしみ|はっぱ子|魚住りえ|海渡みなみ|佐藤くみこ|中島歩|椎名さん|自縛礼|ゆぅ|えむちゃんねる|あめゆ|村上ヨウ|熊崎友香|津田千代子|サラヨウコ|古沢久美子|ユヅル|沼尾ひろ子|中嶋璃來|萩柚月|日髙徹郎|水野 純也|青風マヲ|あきらの|遠山|七味春五郎|ゆきの声|福島美智子|ユウナ|Satow K|月嶋紫乃|tetu9221|WatanabeTomoaki|ひなまつりり|斉藤英治|Naomi Yamato|五十嵐和子|松本夕紀|加賀佑治|Rino|鈴木優|江越彬紀|影森ユリシス|by Simon|ume kura|春山いほ|Meg|岡正子|近藤サト|コンざぶろう|森川弘一|和氣麻乃|ごまババ|斉藤ゆき子|山木梨可|犬塚啓太|萩原みどり|津野まさい|深山ノ|池渕厚子|Tomoko Mukai|わにこ|ReiTube|haru4564|玉井明日子|申詠み|青空文子|ふじた のりこ|倉橋健|平野啓子|ノリスケ|さくらこ|たけるの|佐和子|小出朋加|にっしー|青波佑典|悦子77歳|スルメホタル|きむらじゅり|ハンプおっさん|富本 ゆり子|いんこ博士|小村美記|Asano|早瀬マミ|なな姫|かたふちまこ|たおの|ディッカン|小久保 寿人|中嶋順子|Rie RiZ|永月しおん|けい子|イサムの|ハノミツル|黒蜜|Yamaoka Yuriko|Tomo-channel|輝 Teru|岩井正|おとぎ先生|中江有里|小島香奈子|ユウの|藤堂裕美子|Mai Voice|嘉音|James Dibartolomeo|amakiyou|緒方桃子|宮下詩麻|山田隆一|大和田悠太|くまのみ|伸び子|小麦。|千代真由美|どあこ|がんもどき|岡部雅子|Miyaの|慶兎|なぎの|とまるあきこ|互ひとみ|5児の父|さちの|中城里香|チャンケー|ナシノ|雛鳥しお莉|冬雪氷菓|トマソマリ|加納恵美子|櫛部妙有|黒沢佳奈|みつあめ|進藤晶子|こばち|くろと ゆうな|akichanbon|大迫ゆかり|koi kurenai|Kokko|こじまゆか|れんぺい|Tsuyako Maeo|竹田りえ|タニー|芥川紬|立川志の太郎|マッハの|高橋映美子|OZY|mysteryman|Tanaka|ゆめにゃん|Ｍｉｒａｎ Ｉｋｅｄａ|鈴木弘子|satomi|つぐの|さとうむつみ|BAKU|小林睦|藤田利和|阿久澤菜々|まぁこと|叶みつき|伊織弓鶴|kou-channel|井上嵩之|百舌トト|ゆあーん|つかさ|kariko kusano|めぇた|Rumi|Leyna|テトミヤ|桃丸みかん|ogawa hide|さっくー|結木かおり|辻さき|武富太郎|もこもこ|風嶋|おおやさん|マミの|すずきみゆき|ノマの|忸田業緒|瑠璃の|佐々木久美子|菜央子|Chiaki|白鳥の朗読|小林志保|レオ　|^Ara$|まきりか|紡木いと|ゆり【|詩馬広健|すない|陽和悠|にし。|yuuka yano|ぐらのーら|よしだしょういん|青年Y|二条　朔|まみっぽ|くすのきツァイト|ゆだまめ|すずらんひろみ|華村 だんご|こいけ小うま|てるお|nagamaro|うてな|蒼鮭|ひーちゃん|どちみ|おすしにぎにぎ|よいやこ|満星ゆかり|Tatsuhiko|ハルの|くろのすけ|^K$|きょんきょん|やまだ|ゆうなの|瀬川|白鳥怜奈|岡本|山岡ゆり子|上田真紗子|大熊英司"""
PERSON = re.compile(PERSON.replace('\n', ''))

# 実際に知名度のある人（テレビ局・大手事務所のアナウンサー、テレビアニメの声優、俳優など。題名かチャンネル名で照合）
KNOWN = re.compile(r'窪田等|魚住りえ|近藤サト|中江有里|進藤晶子|中島歩|平野啓子|日髙徹郎|日高徹郎|西村俊彦|江守徹|宮沢りえ|中嶋朋子|市原悦子|沢城みゆき|渡辺謙|橋爪|壤晴彦|国井雅比古|國井雅比古|浅沼晋太郎|阿座上洋平|岸田今日子|森本レオ|長岡輝子|寺田農|仲代|鳥海浩輔|下野紘|中尾隆聖|井上和彦|竹内由恵|田中瞳|大熊英司|白鳥怜奈|にじさんじ|ホロライブ|hololive')


def name_type(n):
    n = n or ''
    if AUTH_VOICE.search(n) or AUTH_ORG.search(n) or AUTH_OTHER.search(n):
        return 'd_肩書き・権威'
    if USE.search(n):
        return 'a_用途'
    if PERSON.search(n):
        return 'c_個人名'
    if MOOD.search(n):
        return 'b_雰囲気・文芸'
    return 'e_その他'


def main(work, out):
    R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../docs/research/data/')
    base = pd.read_csv(R + 'growth_channels_2026-10-23.csv')
    raw = {}
    for g in glob.glob(os.path.join(work, 'chan_*.jsonl')):
        for l in open(g, encoding='utf-8'):
            j = json.loads(l)
            if not j.get('error'):
                raw[j['chid']] = j
    rows = []
    for r in base.itertuples():
        j = raw.get(r.chid, {})
        n = r.name if isinstance(r.name, str) else ''
        desc = j.get('desc') or ''
        rec = [x for x in j.get('recent', []) if x.get('views') is not None and x.get('age') is not None]
        r3 = [x for x in rec if 30 <= x['age'] <= 3 * 365]
        d = dict(chid=r.chid, name=n, subs=r.subs, n_videos=r.n_videos, years=r.years_since_joined,
                 rod_share=r.recent_share_rodoku_or_literature, name_type=name_type(n),
                 f_auth_voice=bool(AUTH_VOICE.search(n)), f_auth_org=bool(AUTH_ORG.search(n) or AUTH_OTHER.search(n)),
                 f_use=bool(USE.search(n)), f_person=bool(PERSON.search(n)), f_mood=bool(MOOD.search(n)), f_hint=bool(HINT.search(n)),
                 known=bool(KNOWN.search(n)) or (r.subs >= 100000 if r.subs == r.subs else False),
                 desc_auth_voice=bool(AUTH_VOICE.search(desc)),
                 recent3y_n=len(r3),
                 recent3y_med_views=float(np.median([x['views'] for x in r3])) if r3 else np.nan,
                 recent3y_med_vpd=float(np.median([x['views'] / x['age'] for x in r3])) if r3 else np.nan)
        rows.append(d)
    c = pd.DataFrame(rows)
    c['subs_per_video'] = c.subs / c.n_videos.where(c.n_videos > 0)
    c.to_csv(out, index=False)
    print(len(c), c[c.rod_share >= 0.5].name_type.value_counts().to_dict())


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
