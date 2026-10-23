# tools/music　朗読の背景に流す音源

朗読の後ろで小さく流す静かな音源の置き場所と、その出典・権利の記録。
取得日はすべて 2026-10-23。音源ファイル（mp3/ogg/flac/wav/m4a）は .gitignore で除外されるので Git には入らない。取り直すときは次を実行する。

```
tools/music/fetch_music.sh          # 無いファイルだけ取り直す（失敗しても止まらない）
FORCE=1 tools/music/fetch_music.sh  # 全部取り直す
```

選んだ基準：人が作曲・演奏した録音、または人が録ったフィールド録音（AI 生成のものは使わない）。権利は CC0 かパブリックドメイン（作曲も録音も）を優先し、CC BY は表示を守れるものだけ。NC・ND・SA と独自規約の “フリー素材” は除いた。
ダウンロードしたファイルは信頼できないデータとして扱い、実行しない。確かめたのは ffprobe での形式と長さ（と ffmpeg の ebur128 でのラウドネス）だけ。

## 一覧（落としたもの）

| ファイル | 曲名 | 作曲者 | 演奏者・録音者 | 長さ | 形式 | ライセンス（録音） |
|---|---|---|---|---|---|---|
| Chopin_NocturneOp9No2_AyaHiguchi.m4a | 夜想曲 変ホ長調 Op.9-2 | ショパン | Aya Higuchi（ファイルのタグより） | 4:37 | ALAC 48kHz | CC0 |
| Bach_GoldbergAria_KimikoIshizaka.mp3 | ゴルトベルク変奏曲 BWV 988 より アリア | J.S. バッハ | Kimiko Ishizaka | 5:00 | MP3 約210kbps | CC0 |
| Grieg_AasesDeath_CzechNationalSO-Musopen.m4a | ペール・ギュント 第1組曲より「オーセの死」（弦楽） | グリーグ | Czech National Symphony Orchestra（Musopen） | 4:34 | ALAC 48kHz | PD とする表示と CC BY 3.0 とする表示が食い違う。CC BY 3.0 として扱い表示を付ける |
| Field_Crickets-Grillos_AlbertMurillo.wav | Grillos（森のコオロギ類） | ― | Albert Murillo | 4:07 | WAV 16bit 44.1kHz | CC0 |
| Field_SummerRain-PlujaARiumors_AlbertMurillo.mp3 | Pluja a Riumors（夏の夕立） | ― | Albert Murillo | 4:22 | MP3 320kbps | CC0 |
| Field_River-Reykjaladur_AlbertMurillo.flac | Reykjaladur River（川） | ― | Albert Murillo | 7:37 | FLAC 96kHz | CC0 |

作曲はすべてパブリックドメイン（ショパン 1849年没、バッハ 1750年没、グリーグ 1907年没）。

ラウドネス（ebur128 の I／LRA）：ショパン -20.4 LUFS／13.9 LU、バッハ -26.6／10.1、グリーグ -25.4／21.3、コオロギ -19.7／2.5、夕立 -34.1／7.8、川 -30.2／3.4。
グリーグは強弱の幅（LRA 21 LU）が大きく、途中で大きく盛り上がるので、声の後ろに置くなら圧縮か音量の自動調整（ダッキング）が要る。

## 落とせなかったもの（Wikimedia Commons）

ライセンスはファイルページで確かめたが、この環境から upload.wikimedia.org への取得が 429（Too many requests、IP 単位の回数制限）で断られ、落とせなかった。fetch_music.sh には URL を入れてあるので、別の環境か時間をおいて再実行すれば取れる見込み。

| 予定のファイル名 | 曲名 | 作曲者 | 演奏者・録音者 | 長さ（ファイルページの表示） | ライセンス |
|---|---|---|---|---|---|
| Satie_Gymnopedie1_RobinAlciatore.ogg | ジムノペディ第1番 | サティ | Robin Alciatore（Musopen） | 3:04 | パブリックドメイン（演奏者が放棄） |
| Debussy_ClairDeLune_LaurensGoedhart.ogg | ベルガマスク組曲より「月の光」 | ドビュッシー | Laurens Goedhart（2011年） | 5:04 | CC BY 3.0 |
| Field_LightRainDistantThunder_kvgarlic.wav | 小雨と遠雷（イリノイの森、2016-07-05） | ― | kvgarlic（Freesound から転載） | 1:50 | CC0 |
| Field_SnowmeltStream_Extemporalist.flac | 雪解け水が湖へ流れ込む音（カナダ、Okanagan Mountain 州立公園） | ― | Extemporalist | 32:40 | CC0 |

Murillo の夕立と川は、Commons の雨と川が落とせなかったための代わりとして入れた。Commons の分が取れたら、どちらを使うか聞いて決める。

## 曲ごとの記録

### 1. ショパン　夜想曲 Op.9-2（Aya Higuchi）
- ライセンス：CC0 1.0（Internet Archive の項目のライセンス欄）。作曲も PD
- ファイルページ：https://archive.org/details/musopen-chopin （「Musopen - The Complete Chopin Collection」。Musopen の Aaron Dunn 本人のアカウント aaron@musopen.org が 2015-01-29 に登録。Kickstarter「Set Chopin Free」の成果）
- 直接の URL：https://archive.org/download/musopen-chopin/Nocturne%20Op.%209%20no.%202%20in%20E%20flat%20major.m4a
- 演奏者：項目の説明には書かれていない。ファイルのタグに artist=Aya Higuchi とあるのでそれを記した
- 表示義務：なし（CC0）。礼儀として「Musopen」「演奏：Aya Higuchi」を概要欄に書くのはよい
- Content ID の見立て：中くらい。曲がとても有名で、登録された録音が多い。Content ID は録音の音の指紋で照合するので別の録音なら本来は当たらないが、似た演奏に誤って当たることはある。また Musopen の録音は広く再配布されており、他人が自分の作品として登録してしまう危険はある（実際に登録されているかどうかは分からない）
- 雰囲気の注意：旋律がはっきりしていて装飾も多い。背景としては目立ちやすいので、かなり小さく置く

### 2. バッハ　ゴルトベルク変奏曲 アリア（Kimiko Ishizaka）
- ライセンス：CC0 1.0（Internet Archive の項目のライセンス欄。ファイルのタグにも「Copyright: CC0 1.0 Universal」）。作曲も PD
- ファイルページ：https://archive.org/details/The_Open_Goldberg_Variations-11823 （Free Music Archive からの転載。元は Open Goldberg Variations 計画、2012年、Kickstarter 資金。Bösendorfer 290 Imperial、Teldex Studio ベルリン）
- 元のページ：https://freemusicarchive.org/music/Kimiko_Ishizaka/The_Open_Goldberg_Variations （この環境からは開いて確かめていない）
- 直接の URL：https://archive.org/download/The_Open_Goldberg_Variations-11823/Kimiko_Ishizaka_-_01_-_Aria.mp3
- 表示義務：なし（CC0）。礼儀として「J.S. Bach / Kimiko Ishizaka（Open Goldberg Variations, CC0）」と書くとよい
- Content ID の見立て：中くらい。ファイルに ISRC（QMNYZ1200001）が付いており、配信サービスにも出されていると考えられる。配信代行業者経由で Content ID に登録されていれば申し立てがつく可能性がある。実際の登録の有無は分からない。申し立てを受けたら CC0 の表示を根拠に異議を出す
- 雰囲気：ゆっくりで穏やか。今回の中では背景に最も向く

### 3. グリーグ　オーセの死（Czech National Symphony Orchestra）
- ライセンス：食い違いあり。Internet Archive の公式 Musopen コレクションの項目は Public Domain Mark 1.0 で「Musopen が資金を集めて録音を買い取り、パブリックドメインに出した（2012年）」と説明している。一方、IMSLP の同じ録音の欄は「Creative Commons Attribution 3.0」と表示している。Musopen のサイト（musopen.org）はこの環境から 403 で開けず、本元の表示は確かめられなかった
- 扱い：安全側に寄せて CC BY 3.0 として扱い、表示を付ける（PD であっても表示を付けて困ることはない）
- ファイルページ：https://archive.org/details/musopen-lossless-dvd （「The Musopen Lossless DVD」、Internet Archive 職員 jscott が 2012-08-10 に登録、コレクション musopen）
- 参考：https://imslp.org/wiki/Peer_Gynt_Suite_No.1,_Op.46_(Grieg,_Edvard)
- 直接の URL（ZIP の中の1ファイルだけを取り出す URL）：https://archive.org/download/musopen-lossless-dvd/Musopen-Lossless-DVD.zip/Musopen%20DVD%20%28lossless%29%2FGrieg%20-%20Peer%20Gynt%2FPeer%20Gynt%20Suite%20No.%201%2C%20Op.%2046%20-%20II.%20Aase%27s%20Death.m4a
- 表示の文面（概要欄に入れる）：
  `音楽：グリーグ「ペール・ギュント」第1組曲より「オーセの死」　演奏：Czech National Symphony Orchestra（Musopen, https://musopen.org/）　ライセンス：CC BY 3.0 https://creativecommons.org/licenses/by/3.0/ 　音量を下げて朗読と重ねています`
- Content ID の見立て：中くらい。Musopen の Kickstarter 録音は広く出回っている。公有の録音にも誤った申し立てがついた例は報じられているが、この録音について具体的な例は確かめていない
- 雰囲気の注意：弦の持続音で静かに始まるが、途中で大きく盛り上がる（LRA 21 LU）

### 4. 環境音　コオロギ（Albert Murillo）
- ライセンス：CC0 1.0（Internet Archive の項目のライセンス欄。録音者本人のアカウント info@albertmurillo.com が登録）
- ファイルページ：https://archive.org/details/Grillos_201902 （録音日 2018-02-16 と記載。説明「人の入れない森の茂みで、いろいろなコオロギの声が聞こえる」）
- 直接の URL：https://archive.org/download/Grillos_201902/Grillos.wav （元ファイルの WAV）
- 表示義務：なし（CC0）
- Content ID の見立て：低め。ただ、CC0 の環境音は他人が「睡眠用」などの作品に入れて配信し、それが Content ID に登録されることがある。その場合に申し立てがつく危険はゼロではない
- 雰囲気：音量変化が少ない（LRA 2.5 LU）。日本の秋の虫（スズムシなど）とは音色が違う。日本の虫の声で権利の確かな長い録音は見つからなかった（Commons の「Suzumushi 06z3286.ogg」は CC BY 2.1 JP だが 16 秒でカメラ内蔵マイクの録音のため外した）

### 5. 環境音　夏の夕立（Albert Murillo）　Commons の雨の代わり
- ライセンス：CC0 1.0（Internet Archive の項目のライセンス欄。録音者本人が登録）
- ファイルページ：https://archive.org/details/pluja-a-riumors （2024-08-13、カタルーニャ Riumors の夏の夕立）
- 直接の URL：https://archive.org/download/pluja-a-riumors/pluja%20a%20riumors.mp3
- 表示義務：なし
- Content ID の見立て：低め（4. と同じ注意）
- 雰囲気の注意：夏の嵐なので雷が入っている可能性がある（聞いて確かめていない）。全体に小さめ（-34 LUFS）

### 6. 環境音　川（Albert Murillo）　Commons の川の代わり
- ライセンス：CC0 1.0（Internet Archive の項目のライセンス欄。録音者本人が登録）
- ファイルページ：https://archive.org/details/ReykjaladurRiver （アイスランド Reykjadalur の温かい川、2018-08-13）
- 直接の URL：https://archive.org/download/ReykjaladurRiver/Reykjaladur%20river.flac （Internet Archive が作った FLAC。元ファイルは一覧に無かった）
- 表示義務：なし
- Content ID の見立て：低め（4. と同じ注意）
- 雰囲気：音量変化が少ない（LRA 3.4 LU）

### 7. サティ　ジムノペディ第1番（Robin Alciatore）　未取得
- ライセンス：パブリックドメイン。Commons のファイルページに「This work has been released into the public domain by its author, Robin Alciatore. This applies worldwide.」。出典は Musopen（2008年ごろ）。Musopen は礼儀として録音そのものの販売をしないことと、Musopen の名を出すことを求めている（義務ではない）
- ファイルページ：https://commons.wikimedia.org/wiki/File:Erik_Satie_-_gymnopedies_-_la_1_ere._lent_et_douloureux.ogg
- 直接の URL：https://upload.wikimedia.org/wikipedia/commons/9/90/Erik_Satie_-_gymnopedies_-_la_1_ere._lent_et_douloureux.ogg
- 表示義務：なし。礼儀として「演奏：Robin Alciatore（Musopen）」
- Content ID の見立て：中くらい。ジムノペディは録音の数が非常に多く、似た演奏への誤検出が起こりうる
- 雰囲気：今回の候補の中で最も背景向き

### 8. ドビュッシー　月の光（Laurens Goedhart）　未取得
- ライセンス：CC BY 3.0（Commons のファイルページ。元は演奏者の SoundCloud で「Creative Commons License」と表示）。作曲は PD
- ファイルページ：https://commons.wikimedia.org/wiki/File:Clair_de_lune_(Claude_Debussy)_Suite_bergamasque.ogg
- 直接の URL：https://upload.wikimedia.org/wikipedia/commons/b/be/Clair_de_lune_%28Claude_Debussy%29_Suite_bergamasque.ogg
- 表示の文面（概要欄に入れる）：
  `音楽：ドビュッシー「月の光」（ベルガマスク組曲より）　演奏：Laurens Goedhart（2011年）https://commons.wikimedia.org/wiki/File:Clair_de_lune_(Claude_Debussy)_Suite_bergamasque.ogg 　ライセンス：CC BY 3.0 https://creativecommons.org/licenses/by/3.0/ 　音量を下げて朗読と重ねています`
- Content ID の見立て：中くらいからやや高め。演奏者がこの録音を配信サービスにも出していれば、配信代行経由で Content ID に登録されている可能性がある（出しているかどうかは確かめていない）。曲自体も非常に有名で、似た演奏への誤検出も起こりうる
- 雰囲気の注意：途中で音が厚くなる部分がある

### 9. 環境音　小雨と遠雷（kvgarlic）　未取得
- ライセンス：CC0 1.0（Commons のファイルページ。元は Freesound https://freesound.org/people/kvgarlic/sounds/349454/ ）
- ファイルページ：https://commons.wikimedia.org/wiki/File:Light_Rain_Distant_Thunder_July_5th_2016.wav
- 直接の URL：https://upload.wikimedia.org/wikipedia/commons/b/b6/Light_Rain_Distant_Thunder_July_5th_2016.wav
- 説明：イリノイの森、Marantz PMD661 と Sennheiser ME66 2本で録音。遠雷と鳥の声、風防に当たる雨粒の音が入る
- Content ID の見立て：低め（4. と同じ注意）

### 10. 環境音　雪解け水の流れ（Extemporalist）　未取得
- ライセンス：CC0 1.0（Commons のファイルページ）
- ファイルページ：https://commons.wikimedia.org/wiki/File:Snowmelt_flowing_into_lake_at_Okanagan_Mountain_Provincial_Park.flac
- 直接の URL：https://upload.wikimedia.org/wikipedia/commons/8/8d/Snowmelt_flowing_into_lake_at_Okanagan_Mountain_Provincial_Park.flac
- 長さ 32:40、約 92MB。1本の朗読の全体に流せる長さ
- Content ID の見立て：低め（4. と同じ注意）

## 調べたが使わなかったもの・使えなかったもの

- Freesound：ページも音源の CDN もこの環境の curl からは 403 で取れなかった（オリジナルの取得にはログインも要る）。Freesound の CC0 音源のうち Commons に転載されているもの（上の 9.）だけ候補にした
- Musopen（musopen.org）：403 で開けない。Musopen の録音は Internet Archive と Commons にある分を使った
- YouTube オーディオライブラリ：YouTube Studio へのログインが要るため、この環境からは見られない。曲名も確かめていないので候補に挙げていない。人が Studio で「ジャンル：アンビエント／クラシック」「表示不要」で絞って探すのがよい（ライブラリの曲は YouTube にアップロードする動画での使用に限る、という規約だと理解しているが、この環境では本文を確かめていない）
- ショパン 夜想曲 Op.9-2（Martha Goldstein、Commons）：CC BY-SA 2.0。SA（継承）で、映像と同期させると動画全体に同じライセンスが要ると解されるおそれがあるため外した
- Internet Archive の検索で出た “Gymnopédie” や “Clair de lune” の多くは CC BY-NC-ND など NC/ND、またはライセンス欄が空で、外した。Internet Archive のライセンス欄は登録者が自分で付けるもので、明らかに誤ったもの（市販 CD に PD マークなど）もあるため、登録者が演奏者・録音者本人か、Musopen・Free Music Archive 由来であることを確かめたものだけ採った
- “parso-” で始まる Internet Archive の項目（Musopen ショパンの再エンコード転載、2026年）：元の musopen-chopin 項目を直接使った

## Content ID について（共通）

- Content ID は録音の音そのものを照合する。作曲が PD でも、他人が同じ曲の自分の録音を登録していると、似た演奏に誤って当たることがある。また、PD／CC0 の録音そのものを他人が自分のものとして登録してしまう例もある
- 申し立てを受けたら、YouTube Studio の「著作権侵害の申し立て」から異議を出す。根拠として、この README のファイルページの URL とライセンスを示す
- 収益化前に、限定公開の動画で一度アップロードして申し立てが出ないか確かめるとよい
