#!/usr/bin/env bash
# サムネイル用の日本語フォント（IPAex明朝・IPAexゴシック）を取得する。
# ライセンス：IPAフォントライセンス v1.0（商用利用・再配布可）。
# https://moji.or.jp/ipafont/
set -euo pipefail
DEST="${1:-$(dirname "$0")/fonts}"
mkdir -p "$DEST"
if [ -f "$DEST/ipaexm.ttf" ]; then echo "already: $DEST/ipaexm.ttf"; exit 0; fi
TMP="$(mktemp -d)"
curl -sS -L --max-time 300 -o "$TMP/ipaex.zip" "https://moji.or.jp/wp-content/ipafont/IPAexfont/IPAexfont00401.zip"
unzip -o -q "$TMP/ipaex.zip" -d "$TMP"
cp "$TMP"/IPAexfont*/ipaexm.ttf "$TMP"/IPAexfont*/ipaexg.ttf "$DEST/"
cp "$TMP"/IPAexfont*/IPA_Font_License_Agreement_v1.0.txt "$DEST/" 2>/dev/null || true
rm -rf "$TMP"
echo "fonts: $DEST"
