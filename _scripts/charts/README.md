# _scripts/charts

記事本文に埋め込むSVGの図を生成するスクリプト。`_scripts/` はアンダースコア始まりなので
Jekyll のビルド対象に入らない（`_config.yml` の `exclude` を触る必要はない）。

対象は「データを持つ図」と「Mermaidだと崩れる構造図」だけ。フロー・シーケンス・状態遷移など
Mermaidで書けるものは本文へ ` ```mermaid! ` で直接書く。アイキャッチは対象外
（[アイキャッチ画像生成ワークフロー](../../docs/eyecatch-image-generation-workflow.md) を参照）。

## サイズの決め方

図は `<img>` として一様に拡縮されるだけなので、**座標系の単位をモバイルでの実pxに近づける**。
記事本文での実表示幅は次のとおり。

| | 実表示幅 | viewBox幅400のときの倍率 |
| :--- | ---: | ---: |
| デスクトップ | 560px（`.chart` の `max-width`） | 1.40倍 |
| スマホ（390px端末） | 約330px | 0.83倍 |

`.chart` で表示幅に上限をかけないと、本文幅は約860px（`$content-width: 920px`）まで広がり、
モバイルとの倍率差が2.6倍になってどちらかが必ず破綻する。上限を入れて1.7倍まで縮めてある。

そのため、マークダウン側では **必ず kramdown の IAL でクラスを付ける**。

```markdown
![altテキスト](/assets/images/posts/<slug>/figure.svg){: .chart}
```

スタイルは [`_sass/misc/chart.scss`](../../_sass/misc/chart.scss)。

## 使い方

Python 3 の標準ライブラリだけで動く。追加のインストールは不要。

```bash
python3 _scripts/charts/2026-07-14-win-rate-sample-size-statistics.py   # 個別
for f in _scripts/charts/[0-9]*.py; do python3 "$f"; done               # 全部
python3 _scripts/charts/check.py                                        # 当たり判定チェック
```

出力先は `assets/images/posts/<slug>/` で、既存ファイルは上書きされる。

`check.py` は、この環境でSVGをラスタライズできないことの埋め合わせとして、
viewBoxからのはみ出し・テキスト同士の重なり・モバイルでの最小文字サイズを座標から機械的に見る。
目視の代わりにはならないので、最後は `docker compose up` で実機幅を確認すること。

```bash
docker compose run --rm jekyll bundle exec jekyll build
```

## ファイルの対応

| スクリプト | 記事 | 出力 |
| :--- | :--- | :--- |
| `2026-06-06-vercel-frontend-selection.py` | Vercelフロントエンド選定（日英） | `bandwidth-cost.svg` / `-en.svg` |
| `2026-06-08-harness-engineering-guide.py` | ハーネスエンジニアリング（日英） | `harness-structure.svg` / `-en.svg` |
| `2026-06-10-claude-mythos-fable.py` | Mythos/Fable | `benchmark-comparison.svg` |
| `2026-07-14-win-rate-sample-size-statistics.py` | 勝率と標本サイズ | `confidence-interval.svg` / `beta-posterior.svg` |
| `2026-07-20-kimi-k3-vs-fable-gpt.py` | Kimi K3比較 | `benchmark-comparison.svg` / `pricing-comparison.svg` |

ファイル名は記事のslugに合わせる。日英で同じ図を使う記事は1スクリプトで両方を出力する。

## 書くときの約束

- `viewBox` の幅は `common.py` の `VB_W`（400）で固定。個別に変えない
- フォントサイズは `common.py` の `FS` から取る。小さくしたくなったら、まず情報量を減らす
- 1行のラベルは日本語で12文字、英数字で28文字まで。長い説明は本文へ逃がす
- 1枚に載せる系列は3つまで。4つ以上はパネルを分ける
- 目盛りは5本まで
- 横並びの凡例は幅が足りない。`legend_stacked()` で縦に積む
- 棒グラフの軸は必ず0から始める。途中で切ると差が誇張される
- 縦軸を2本持つ図は作らない。単位が違う指標はパネルを分ける
- 同じ形のパネルを積む図は `bar_panel()` を使う。パネル描画を個別に書かない
- 配色は `common.py` に寄せる。個別スクリプトで色を直書きしない
- カテゴリカルの色はスロット順（S1→S2→S3）に使い、循環させない
- 数値の出典と年月を脚注に入れる
- `svg()` の `desc` には図の内容を文章で書く。記事側の `alt` とは別に読み上げへ渡る

## 料金・ベンチマークの更新

`_data/stale_watch.yml` に載っている記事の図は、記事本文を直すときに図も一緒に差し替える。
数値はスクリプト上部の定数にまとめてあるので、そこを書き換えて再生成する。
脚注の年月表記も忘れずに更新すること。
