# アクセスデータの取得

GA4とSearch Consoleから、記事のネタ選びと編集判断に使うレポートを手元へ生成する。

出力先は `.analytics/`。このディレクトリは `.gitignore` 済みで、公開リポジトリには入らない。
数値をコミットしない前提の構成なので、出力をリポジトリへ足さないこと。

## セットアップ

### 1. Google Cloud

プロジェクトを1つ用意し、次の2つのAPIを有効化する。

- Google Analytics Data API
- Google Search Console API

同じプロジェクトでサービスアカウントを作成し、JSON鍵をダウンロードする。
**GCP側のロール（編集者・閲覧者など）は付けなくてよい。** 権限はGA4とSearch Console
それぞれの管理画面で与える。

鍵はリポジトリの外へ置く。

```bash
mkdir -p ~/.config/waka-ds-analytics
mv ~/Downloads/xxxxx.json ~/.config/waka-ds-analytics/service-account.json
chmod 600 ~/.config/waka-ds-analytics/service-account.json
```

### 2. GA4 側の権限

GA4管理画面 > 管理 > プロパティのアクセス管理 で、サービスアカウントのメールアドレス
（`...@....iam.gserviceaccount.com`）を **閲覧者** として追加する。

同じ画面でプロパティIDを控える。`_config.yml` にある `G-XNP1RBTG9C` は計測用の別物で、
APIには使えない。

### 3. Search Console 側の権限

Search Console > 設定 > ユーザーと権限 で、同じメールアドレスを **制限付き** として追加する。
サービスアカウントでもここへ手で登録する必要がある。

### 4. 設定値を書く

```bash
mkdir -p .analytics
cat > .analytics/config.env <<'EOF'
WAKA_DS_GA4_PROPERTY_ID=123456789
WAKA_DS_GSC_SITE_URL=sc-domain:waka-ds.com
EOF
```

`WAKA_DS_GSC_SITE_URL` は登録形式に合わせる。ドメインプロパティなら
`sc-domain:waka-ds.com`、URLプレフィックスなら `https://waka-ds.com/`。

鍵を既定のパス以外へ置いた場合は `WAKA_DS_GA_CREDENTIALS` も書く。

### 5. 依存パッケージ

```bash
python3 -m venv .analytics/venv
.analytics/venv/bin/pip install -r _scripts/analytics/requirements.txt
```

## 実行

```bash
.analytics/venv/bin/python _scripts/analytics/fetch.py
.analytics/venv/bin/python _scripts/analytics/fetch.py --days 90
```

出力は次のとおり。

```
.analytics/
  latest-ja.md          最新レポート（日本語記事）
  latest-en.md          最新レポート（英語記事）
  2026-08-08/
    report-ja.md
    report-en.md
    raw/*.json          再集計用の生データ
```

前回から何が変わったかだけを読みたいときは `watch.py` を使う（次節）。

## 変化だけを追う

`watch.py` は `fetch.py` と同じ取得をしてレポートを更新したうえで、`.analytics/` に
残っている直前の実行結果と比べ、変わった点だけを標準出力へ出す。

```bash
.analytics/venv/bin/python _scripts/analytics/watch.py

# 取得せず、すでにある直近2回のスナップショットだけを比べ直す
.analytics/venv/bin/python _scripts/analytics/watch.py --no-fetch
```

出力はこの形になる。

```
前回 2026-09-04 との比較（今回 2026-09-05）
- 検索表示（週次） 21 → 41（+95%） 2026-08-17週 → 2026-08-24週
- 平均順位 56.1 → 37.7（18.4位改善） 2026-08-17週 → 2026-08-24週
- bing / organic セッション（週次） 13 → 19（+46%） 2026-08-17週 → 2026-08-24週
詳細は .analytics/latest-ja.md
```

見ているのは、Google検索の週次表示回数と平均順位、検索エンジン別の週次セッション、
伸び／落ちの一覧へ新しく入った記事、前回になかった検索クエリの4つ。しきい値を
超えるものが1つもなければ `前回 YYYY-MM-DD と比べて大きな変化なし。` の1行で終わる。
基準は `watch.py` の先頭にまとめてある。

週は7日そろっている週だけを比べる。取得範囲の端にかかる週を混ぜると、
落ちたのか、まだ日数が足りないだけなのかが区別できない。

進捗と失敗は標準エラーへ出す。標準出力は差分だけなので、そのままファイルへ落とせる。

## 定期実行

思い出したときに実行する運用だと、検索からの断落に数週間気づけない。
月1回 cron で回し、差分の行だけを読む。

`crontab -e` へ次の1行を足す（毎月1日の午前9時）。パスは環境に合わせて置き換える。

```cron
0 9 1 * * /home/kaito/projects/Kaito-ickw.github.io/.analytics/venv/bin/python /home/kaito/projects/Kaito-ickw.github.io/_scripts/analytics/watch.py >> /home/kaito/projects/Kaito-ickw.github.io/.analytics/watch.log 2>> /home/kaito/projects/Kaito-ickw.github.io/.analytics/watch-error.log
```

cron は PATH もカレントディレクトリも当てにできないため、venv の python と
スクリプトはどちらも絶対パスで書く。出力先の `.analytics/` はスクリプト側が
リポジトリの位置から決めるので、`cd` は要らない。

WSLでは cron が動いていないことがある。`service cron status` で確認し、
止まっていれば `sudo service cron start` で起動する。Windowsを再起動すると
また止まるので、動いているかを最初に疑う。

### どこを読むか

| 見るもの | 中身 |
| :--- | :--- |
| `.analytics/watch.log` | 実行ごとの差分。ここだけ読めばよい |
| `.analytics/latest-ja.md` | 差分で気になった点を掘るときのレポート本体 |
| `.analytics/watch-error.log` | 失敗したときの原因 |

`watch.log` は追記される。各回の1行目に「前回 … との比較（今回 …）」が入るので、
末尾から遡って読む。

### 失敗したとき

終了コードが1なら差分は出ていない。`watch-error.log` の末尾を見る。

- `設定エラー` … `.analytics/config.env` か鍵のパス。セットアップの4を見直す
- `取得に失敗した` … 認証か権限。サービスアカウントの登録を疑う（同じログに手順が出る）
- ログが空のまま更新されない … cron 自体が動いていない。上のWSLの注意を見る

数か月ぶんの実行が飛んでいても、`.analytics/` に残っている直前のスナップショットと
比べるだけなので、そのまま実行してよい。ただし比較の間隔は空くほど粗くなる。

## レポートの読み方

| セクション | 使いどころ |
| :--- | :--- |
| 検索での見え方の推移 | 週ごとの表示・順位。ある週を境に落ちていたらサイト全体の問題 |
| 流入元の推移 | 検索エンジン別の週次セッション。片方だけ落ちたかを見る |
| 伸びている記事 | 追記・関連記事を書く価値がある |
| 落ちている記事 | 情報が古い可能性。`_data/stale_watch.yml` の優先度づけに使う |
| 取りこぼしている記事 | 検索に出ているのに読まれていない。タイトル改訂か追記の候補 |
| 記事化の候補になる検索クエリ | 新規記事のネタ。受け皿がないクエリと、順位が低いクエリの2種類 |
| 記事一覧 | 全体の把握 |
| 流入チャネル | サイト全体の傾向 |

期間の合計だけを見ていると、緩やかな減衰と、ある週を境にした断落を取り違える。
先に「検索での見え方の推移」と「流入元の推移」を見て、記事単位の話なのか
サイト全体の話なのかを決めてから、以降のセクションを読む。

## 制約

- GA4もSearch Consoleも直近数日のデータは確定しない。期間の終端は既定で3日前
- 閲覧の少ないページは行そのものが返らないことがある。レポートに出ない＝ゼロ、ではない
- Search Consoleがさかのぼれるのは16ヶ月まで。ただしプロパティを登録する前の実績は
  遡って入らないため、登録直後は空になる（`waka-ds.com` のドメインプロパティは 2026-08-08 登録）
- 検索クエリの一部は、個人が特定されうるものとしてGoogle側が返さない。網羅ではなく傾向として読む
- GA4は自動巡回をすべては除けない。1閲覧あたりの滞在が数秒未満の行は人が読んだ数として
  扱わず、記事一覧で `※` を付けて「伸びている記事」からも外している。しきい値は
  `analysis.py` の `MIN_SEC_PER_VIEW`
- 手動による対策（ペナルティ）の有無はAPIから取れない。サイト全体で順位が崩れたときは
  Search Consoleの画面で確認する

## 候補の基準を変える

「どれを候補として挙げるか」のしきい値は `analysis.py` の先頭にまとめてある。
表の見た目を変えたいときは `render.py`。
