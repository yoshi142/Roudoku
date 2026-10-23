#!/usr/bin/env python3
"""詩集の XHTML から一篇を切り出して poems.json に書く（tools/poem_scripts.py の入力）。

使い方: 下の POEMS に、(キー, 青空文庫の XHTML の URL か ファイル, 開始の文字列, 終了の文字列) を書いて実行する。
開始・終了は本文中の文字列（終了の手前まで）。詩集は「［＃改ページ］」で終わる篇が多い。
  python3 tools/extract_poems.py > poems.json
2026-10-22 に trial-09〜11 の詩を作ったときの例（雪、風景、竹、汚れつちまつた悲しみに、初恋、あどけない話、永訣の朝）を残してある。
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aozora_script import fetch, main_text

BASE = 'https://www.aozora.gr.jp/cards/'
POEMS = [
    ('yuki', BASE + '001749/files/55797_55505.html', '太郎を眠らせ', '［＃改ページ］'),
    ('fukei', BASE + '000136/files/52348_42039.html', None, None),
    ('take', BASE + '000067/files/859_21656.html', '光る地面に竹が生え', '　　　　　　○'),
    ('yogore', BASE + '000026/files/894_28272.html', '汚れつちまつた悲しみに\n', '［＃改ページ］'),
    ('hatsukoi', BASE + '000158/files/1508_18509.html', 'まだあげ初', '　　狐のわざ'),
    ('adokenai', BASE + '001168/files/46669_25695.html', '智恵子は東京に空が無い', '［＃改ページ］'),
    ('eiketsu', BASE + '000081/files/1058_15403.html', 'けふのうちに', '［＃改ページ］'),
]


def cut(t, start, end):
    if start is None:
        return t.strip('\n')
    i = t.find(start)
    j = t.find(end, i + 1)
    assert i >= 0 and j > i, (start, end)
    return t[i:j].strip('\n')


if __name__ == '__main__':
    out = {k: cut(main_text(fetch(u)), a, b) for k, u, a, b in POEMS}
    print(json.dumps(out, ensure_ascii=False, indent=1))
