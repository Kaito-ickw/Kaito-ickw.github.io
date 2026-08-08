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

## レポートの読み方

| セクション | 使いどころ |
| :--- | :--- |
| 伸びている記事 | 追記・関連記事を書く価値がある |
| 落ちている記事 | 情報が古い可能性。`_data/stale_watch.yml` の優先度づけに使う |
| 取りこぼしている記事 | 検索に出ているのに読まれていない。タイトル改訂か追記の候補 |
| 記事化の候補になる検索クエリ | 新規記事のネタ。受け皿がないクエリと、順位が低いクエリの2種類 |
| 記事一覧 | 全体の把握 |
| 流入チャネル | サイト全体の傾向 |

## 制約

- GA4もSearch Consoleも直近数日のデータは確定しない。期間の終端は既定で3日前
- 閲覧の少ないページは行そのものが返らないことがある。レポートに出ない＝ゼロ、ではない
- Search Consoleがさかのぼれるのは16ヶ月まで。ただしプロパティを登録する前の実績は
  遡って入らないため、登録直後は空になる（`waka-ds.com` のドメインプロパティは 2026-08-08 登録）
- 検索クエリの一部は、個人が特定されうるものとしてGoogle側が返さない。網羅ではなく傾向として読む

## 候補の基準を変える

「どれを候補として挙げるか」のしきい値は `analysis.py` の先頭にまとめてある。
表の見た目を変えたいときは `render.py`。
