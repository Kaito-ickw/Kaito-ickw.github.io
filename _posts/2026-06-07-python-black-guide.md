---
layout: post
title: "Python の Black とは何か ── AI ネイティブ開発でコード整形を自動化する"
subtitle: フォーマッターの役割から設定・VS Code・CIでの使い方までやさしく解説
categories: 開発
tags: ["Python", "Black", "コードフォーマッター", "AIネイティブ開発", "開発環境"]
lang: ja
ref: python-black-guide
---

AI に Python コードを書かせていると、同じプロジェクトの中でも次のような違いが生まれやすい。

- シングルクォートとダブルクォートが混在する
- 引数が1行に詰め込まれる
- 改行や空白の入れ方がファイルごとに違う
- 人間と AI が編集するたびに、関係のない整形差分が発生する

コードは動くため、後回しにしがちな問題だ。しかし、変更量が増えるほどコードレビューが読みにくくなり、本当に確認すべきロジックの変更が埋もれてしまう。

この「コードの見た目」を自動で統一するのが **Black** である。

---

## 結論を先に

Black は、Python コードを決められたスタイルに自動整形する **コードフォーマッター** である。

```bash
black .
```

基本的にはこのコマンドだけで、プロジェクト内の Python ファイルをまとめて整形できる。

Black の役割を一言で表すなら、次のようになる。

> コードの書き方を人間や AI に考えさせず、プロジェクト全体で同じ見た目にする。

Black はバグを見つけるツールではない。コードを高速化するツールでもない。**ロジックはそのままに、表記を統一するためのツール**である。

---

## Black は何をしているのか

Python では、同じ処理をさまざまな見た目で書ける。

たとえば、次のコードは実行できるが、空白や改行が不統一で読みにくい。

### Black を実行する前

```python
from typing import  Any,Dict

def build_prompt(user_name:str,logs:list[dict[str,Any]],model: str='gpt-4.1',max_output_tokens:int=1000):
  messages=[{'role':'system','content':'You are a log analyst.'},{'role':'user','content':f'Analyze logs for {user_name}: {logs}'}]
  return {'model':model,'messages':messages,'max_output_tokens':max_output_tokens}
```

このファイルに Black を実行する。

```bash
black app.py
```

### Black を実行した後

```python
from typing import Any, Dict


def build_prompt(
    user_name: str,
    logs: list[dict[str, Any]],
    model: str = "gpt-4.1",
    max_output_tokens: int = 1000,
):
    messages = [
        {"role": "system", "content": "You are a log analyst."},
        {
            "role": "user",
            "content": f"Analyze logs for {user_name}: {logs}",
        },
    ]
    return {
        "model": model,
        "messages": messages,
        "max_output_tokens": max_output_tokens,
    }
```

処理内容は変えず、次のような部分が自動で修正されている。

- 演算子や型注釈の前後に空白を入れる
- 長い行を複数行に分割する
- インデントを統一する
- 文字列のクォートを原則としてダブルクォートに統一する
- 複数行の引数や要素の末尾にカンマを付ける
- 関数間に必要な空行を入れる

人間が一つずつ直す必要はない。Black を何度実行しても、同じ入力は同じ形式に整えられる。

---

## フォーマッターとリンターの違い

Black を理解するときに最も重要なのが、**フォーマッターとリンターを分けて考えること**である。

| ツールの種類 | 代表例 | 主な役割 |
| :--- | :--- | :--- |
| フォーマッター | Black | 空白・改行・クォートなどを自動整形する |
| リンター | Ruff、Flake8 | 未使用変数や危険な書き方などを検出する |
| 型チェッカー | mypy、Pyright | 型の矛盾を検出する |
| テスト | pytest | 実際の振る舞いが期待どおりか確認する |

たとえば、次のコードを Black に渡しても、論理的なバグは直らない。

```python
def calculate_average(total: float, count: int) -> float:
    return total / count
```

`count` が `0` なら `ZeroDivisionError` が発生するが、これは見た目の問題ではない。Black の担当範囲外である。

Black を導入しても、リンター・型チェック・テストは引き続き必要になる。

```bash
black .
ruff check .
mypy .
pytest
```

それぞれ別の角度からコードを確認するため、組み合わせて使うことで効果を発揮する。

> `ruff format` は Black と同じフォーマッターの役割を持つ。Black を使うプロジェクトで両方のフォーマッターを同時に動かす必要はない。一方、`ruff check` はリンターなので Black と併用できる。

---

## なぜ Black は設定項目が少ないのか

Black は **opinionated formatter** と呼ばれる。日本語にすると「強い方針を持ったフォーマッター」という意味に近い。

一般的なツールでは、インデント・クォート・改行位置などを細かく設定できる。しかし、設定が多いと「どのスタイルにするか」という議論が再び発生する。

Black は設定の自由度を意図的に抑え、ツール側で多くの判断を行う。

```text
この改行はどちらが読みやすいか
シングルクォートとダブルクォートのどちらを使うか
引数の末尾にカンマを付けるか
```

こうした議論をやめて、ロジックや設計のレビューに時間を使うことが Black の思想である。

### デフォルトの行長は88文字

Black のデフォルトでは、1行の長さを **88文字** として整形する。

PEP 8 でよく知られている79文字より少し長い。コード全体が必要以上に縦長になることを避けつつ、横に長すぎないバランスとして採用されている。

ただし、88文字は絶対的な上限ではない。文字列や分割できない式などでは、Black が88文字を超える行を残すこともある。

---

## インストールと基本操作

2026年6月時点の Black は、Black 自体を実行する環境として Python 3.10 以上を必要とする。

### pip を使う場合

```bash
python -m pip install black
```

### uv を使う場合

```bash
uv add --dev black
```

プロジェクトの開発用依存関係として追加しておくと、チームや CI でも同じバージョンを使いやすい。

### ファイルを一つ整形する

```bash
black app.py
```

### ディレクトリ全体を整形する

```bash
black src tests
```

### プロジェクト全体を整形する

```bash
black .
```

環境によって `black` コマンドが見つからない場合は、モジュールとして実行できる。

```bash
python -m black .
```

---

## ファイルを書き換えずに確認する

Black は通常、対象ファイルをその場で書き換える。まず変更内容だけ確認したい場合は `--diff` を使う。

```bash
black --diff .
```

CI などで「整形が必要なファイルがあるか」だけを判定する場合は `--check` を使う。

```bash
black --check .
```

| コマンド | ファイルの書き換え | 用途 |
| :--- | :---: | :--- |
| `black .` | する | ローカルで整形する |
| `black --diff .` | しない | 変更予定の差分を見る |
| `black --check .` | しない | 整形済みか判定する |
| `black --check --diff .` | しない | CIで判定し、差分も表示する |

`--check` は整形が必要なファイルを見つけると終了コード `1` を返す。そのため、CI のチェックとしてそのまま利用できる。

---

## pyproject.toml で設定を共有する

Black の設定は、プロジェクトルートの `pyproject.toml` に記述する。

```toml
[project]
requires-python = ">=3.11"

[tool.black]
line-length = 88
target-version = ["py311"]
extend-exclude = '''
(
  /migrations/
  | /generated/
)
'''
```

主な項目は次のとおり。

| 設定 | 意味 |
| :--- | :--- |
| `line-length` | 基準とする1行の文字数 |
| `target-version` | 対象プロジェクトが対応する Python バージョン |
| `extend-exclude` | 自動生成ファイルなど、追加で除外するパス |

`target-version` は「Black を実行する Python のバージョン」ではなく、**整形対象のコードが対応する Python バージョン**を示す。

設定を増やす前に、まずは Black のデフォルトを使うのがおすすめである。チーム内で特別な理由がある場合だけ変更すると、Black の「スタイル議論を減らす」という利点を維持できる。

---

## VS Code で保存時に自動整形する

毎回ターミナルで `black .` を実行するより、ファイル保存時に自動整形すると使い忘れが減る。

VS Code では **Black Formatter** 拡張機能をインストールし、`.vscode/settings.json` に次の設定を追加する。

```json
{
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.formatOnSave": true
  }
}
```

これで Python ファイルを保存するたびに Black が実行される。

ただし、保存時整形だけに依存すると、拡張機能を入れていないメンバーや AI エージェントが未整形のコードをコミットできてしまう。最終的には CI のチェックも併用した方が確実である。

---

## pre-commit でコミット前に整形する

コミット前に Black を自動実行するなら、`pre-commit` が使える。

`.pre-commit-config.yaml` を作成する。

```yaml
repos:
  - repo: https://github.com/psf/black-pre-commit-mirror
    rev: 26.5.1
    hooks:
      - id: black
        language_version: python3.11
```

その後、フックを有効にする。

```bash
python -m pip install pre-commit
pre-commit install
```

以後は `git commit` の直前に Black が実行される。ファイルが整形された場合は、その変更を確認して再度コミットする。

`rev` には Black のバージョンを固定する。ローカル・pre-commit・CI でバージョンをそろえると、環境ごとに整形結果が変わるリスクを抑えられる。

---

## GitHub Actions で未整形コードを検出する

GitHub 上でも Black を確認するには、`.github/workflows/black.yml` を追加する。

```yaml
name: Black

on:
  push:
  pull_request:

jobs:
  black:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: psf/black@stable
        with:
          options: "--check --diff"
          src: "."
          version: "26.5.1"
```

未整形のコードが含まれているとチェックが失敗し、Black がどこを変更するか差分で確認できる。

CI ではファイルを自動修正するのではなく、`--check` で問題を通知する構成が基本となる。修正はローカルや開発エージェント側で行い、確認したうえでコミットする。

---

## AI ネイティブ開発で Black が役立つ理由

AI ネイティブなアプリ開発では、人間だけでなく複数の AI エージェントがコードを生成・編集する。

各モデルは異なる書き方を返すことがあり、プロンプトで細かいスタイルを指定しても完全には統一できない。ここで Black を使うと、生成元に関係なく最終的な形式をそろえられる。

### 1. プロンプトを短くできる

AI に毎回「ダブルクォートを使う」「1行88文字にする」「末尾カンマを付ける」と指示する必要がなくなる。

スタイルは Black に任せ、AI への指示を要件・設計・エラー処理に集中できる。

### 2. コードレビューでロジックに集中できる

整形だけの差分が減るため、レビューでは次のような本質的な変更を追いやすくなる。

- プロンプトの組み立て方が変わった
- LLM API のタイムアウト処理が追加された
- ログ保存のトランザクション境界が変わった
- ユーザー入力の検証が追加された

### 3. エージェント間の出力を正規化できる

人間、コード生成 AI、リファクタリング用エージェントの全員が異なるスタイルで書いても、最後に Black を通せば同じ形式になる。

```bash
# AI がコードを生成・編集

# 表記を統一
black .

# 静的な問題を検出
ruff check .

# 振る舞いを確認
pytest
```

Black は AI の代わりにコード品質を保証するものではない。しかし、**AI が生む表記のばらつきを機械的に吸収する工程**として非常に相性がよい。

---

## Black を部分的に無効化する方法

特殊なレイアウトを維持したい場合は、`# fmt: skip` でその行だけ整形対象から外せる。

```python
matrix = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]  # fmt: skip
```

複数行を除外する場合は `# fmt: off` と `# fmt: on` で囲む。

```python
# fmt: off
COMMAND_TABLE = {
    "start":  handle_start,
    "stop":   handle_stop,
    "status": handle_status,
}
# fmt: on
```

ただし、例外を増やすとプロジェクト内の統一感が失われる。本当にレイアウト自体に意味がある場合だけ使うのがよい。

---

## 導入時によく起きる問題

### 最初の実行で大量の差分が出る

既存プロジェクトに初めて Black を実行すると、ほぼすべての Python ファイルが変更されることがある。

機能変更と同じコミットに混ぜるとレビューが難しくなるため、**Black の初回適用だけを独立したコミットまたは Pull Request にする**のがおすすめである。

```bash
black .
git add .
git commit -m "Apply Black formatting"
```

### メンバーごとに結果が変わる

Black の大きなスタイルは安定しているが、バージョンによって細かな整形結果が変わる可能性はある。

依存関係、pre-commit、CI で利用する Black のバージョンをそろえ、更新時はチーム全体でまとめて更新する。

### Black がインポート順を整理してくれない

Black はインポート文の見た目は整えるが、標準ライブラリ・外部ライブラリ・自作モジュールの並び替えを担当するツールではない。

インポート順の整理には Ruff の import rules や isort を使う。isort を使う場合は Black と衝突しないように `profile = "black"` を設定する。

```toml
[tool.isort]
profile = "black"
```

### Black を通したから安全だと思ってしまう

Black は通常、整形前後のコードが実質的に同じ構文木になるか安全チェックを行う。しかし、これはアプリケーションの正しさを確認するテストではない。

認証、権限、課金、LLM の出力検証、データベース更新などは、別途テストとレビューが必要である。

---

## おすすめの最小構成

個人開発や小規模チームなら、最初から複雑な設定を用意する必要はない。

### 1. 開発用依存関係に Black を追加

```bash
uv add --dev black
```

### 2. pyproject.toml に対象バージョンだけ記載

```toml
[tool.black]
target-version = ["py311"]
```

### 3. VS Code の保存時整形を有効化

```json
{
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.formatOnSave": true
  }
}
```

### 4. CI で未整形コードを拒否

```bash
black --check .
```

この構成なら、普段は保存時に自動整形され、漏れた場合だけ CI が検出してくれる。

---

## まとめ

| ポイント | 内容 |
| :--- | :--- |
| **Black の正体** | Python コードの見た目を自動統一するフォーマッター |
| **主な対象** | 空白、改行、インデント、クォート、末尾カンマ |
| **対象外** | バグ検出、型チェック、テスト、性能改善 |
| **基本コマンド** | `black .` |
| **確認だけ行う** | `black --check --diff .` |
| **設定ファイル** | `pyproject.toml` の `[tool.black]` |
| **AI開発での価値** | 人間と複数AIの書式差を自動で正規化する |

Black の本当の価値は、コードをきれいに見せることだけではない。

**「どの書き方が正しいか」を議論する時間をなくし、設計・ロジック・テストに集中できる状態を作ること**にある。

AI がコードを書く量が増えるほど、生成されたコードを一定の形式へ戻す機械的な工程が重要になる。Black は、そのためのシンプルで再現性の高い基盤として利用できる。

---

## 参考

- [Black 公式ドキュメント](https://black.readthedocs.io/en/stable/)
- [Black ── Getting Started](https://black.readthedocs.io/en/stable/getting_started.html)
- [Black ── Usage and Configuration](https://black.readthedocs.io/en/stable/usage_and_configuration/the_basics.html)
- [Black ── The Black Code Style](https://black.readthedocs.io/en/stable/the_black_code_style/current_style.html)
- [Black ── Version Control Integration](https://black.readthedocs.io/en/stable/integrations/source_version_control.html)
- [Black ── GitHub Actions Integration](https://black.readthedocs.io/en/stable/integrations/github_actions.html)
- [psf/black GitHub Repository](https://github.com/psf/black)
