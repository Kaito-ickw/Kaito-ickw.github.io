# _scripts/charts

記事本文に埋め込むSVGの図を生成するスクリプト。`_scripts/` はアンダースコア始まりなので
Jekyll のビルド対象に入らない（`_config.yml` の `exclude` を触る必要はない）。

対象は次の2つ。アイキャッチは対象外
（[アイキャッチ画像生成ワークフロー](../../docs/eyecatch-image-generation-workflow.md) を参照）。

| | モジュール | 用途 |
| :--- | :--- | :--- |
| データを持つ図 | `common.py` | 棒グラフ、区間、ベンチマーク比較 |
| 構造図 | `diagram.py` | 構成図、処理フロー、判断の分岐 |

本文へ ` ```mermaid! ` で直接書いてよいのはシーケンス図だけ。`jekyll-spaceship` は Mermaid を
`mermaid.ink` の外部SVGとして `<img>` で読み込むため、表示幅・文字サイズ・ノードの寸法・配色を
制御できない。フローや構成図は `diagram.py` で描く。

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
| `2026-07-29-felix-craft-autonomy.py` | Felix Craftの自律範囲 | `revenue-breakdown.svg` / `autonomy-boundary.svg` |

構造図（`diagram.py`）を使うスクリプトは、記事のslugと同名で以下にある。

`2026-06-13-nodejs-basics-for-vibe-coding` / `2026-06-13-openclaw-personal-ai-agent` /
`2026-06-16-graphai-agent-workflow-engine` / `2026-06-16-notion-database-personal-backend` /
`2026-06-16-spacex-ipo-kardashev-scale` / `2026-06-17-mcp-protocol-overview` /
`2026-06-18-google-workspace-studio-guide` / `2026-06-18-mcp-host-client-server` /
`2026-06-19-mcp-tools-resources-prompts` / `2026-06-20-mcp-json-rpc-lifecycle` /
`2026-06-21-build-mcp-server-python` / `2026-06-22-mcp-local-remote-transports` /
`2026-06-23-mcp-security-operations` / `2026-06-24-gsd-core-ai-coding-workflow` /
`2026-07-22-loop-engineering-roadmap` / `2026-07-23-physical-ai-data-flywheel-agi` /
`2026-07-23-tinker-training-api` / `2026-07-27-graph-engineering-agent-systems` /
`2026-07-29-felix-craft-autonomy`

ファイル名は記事のslugに合わせる。日英で同じ図を使う記事は1スクリプトで両方を出力する。

## 構造図の書き方（diagram.py）

ノードと辺を宣言すると、層の割り当て・ラベルの折り返し・辺の経路まで組み立てる。

```python
from diagram import Section, figure, write_figure

write_figure("2026-06-13-nodejs-basics-for-vibe-coding", "npm-run-dev-flow.svg", figure(
    "npmdev",
    "npm run dev が開発サーバーを起動するまで",   # <title>
    "AIエージェントがnpm run devを実行し、……",    # <desc>。記事の alt とは別に読み上げへ渡る
    [Section(
        nodes=[("agent", "AIエージェント"), ("cmd", "npm run dev", "accent")],
        edges=[("agent", "cmd")],
    )]))
```

- ノードは `(id, ラベル, スタイル)`。スタイルは `box`（既定） / `accent` / `warm` / `cool` /
  `plain` / `decision`。`decision` は分岐で、菱形だと日本語の置き場がないので六角形で描く
- 辺は `(src, dst, ラベル, オプション)`。オプションに `dashed` / `both`（双方向）を書ける
- ラベルの `\n` は明示的な改行になる。それ以外は幅に合わせて自動で折り返す
- 上へ戻る辺と、箱を突き抜けてしまう辺は、左右のチャネルへ自動で迂回する
- 層の並びが意図と違うときは `layers=[[...], [...]]` で明示する

Mermaid の `subgraph` は横に並んで幅が倍になるので、`Section` として縦に積む。

| 形 | 使うもの |
| :--- | :--- |
| フロー・分岐・ループ | `Section(nodes=..., edges=...)` |
| 並列に列挙するだけ | `Section(chips=[...])` |
| 10段を超える一本道 | `Section(steps=[...])` |
| 当事者どうしのやり取り | `sequence(...)` |
| 内包・階層 | `nested(...)` |

1つの層に4つ以上並べると幅が痩せる。自動で折り返すが、折り返した行は「別の層」に見えるので
警告を出す。並列な列挙なら `chips`、そうでなければ図を分割すること。

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
