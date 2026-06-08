---
layout: post
title: "ハーネスエンジニアリングとは何か"
subtitle: Claude Code の Hooks・Ralph Loop・Supervisor Pattern の設計と実装
categories: AI開発
tags: ["ハーネスエンジニアリング", "AIエージェント", "Claude Code", "Ralph Loop", "自動化", "AI開発"]
lang: ja
ref: harness-engineering-guide
---

AIエージェントを実際の開発に使い込んでいくと、ある転換点に気づく。

**問題は、モデルが賢くないことではない。モデルを「どう使わせるか」の設計が追いついていないことだ。**

- エージェントが意図していない操作をファイルに加える
- ループして同じ失敗を繰り返す
- テストを消して「成功」とみなす
- 承認なしに外部サービスを呼び出す
- 何をやったか追跡できない

これらは全部、モデルの問題ではない。モデルの周りに「どういう制約で、どういう情報を渡して、どう評価するか」を設計していないことが原因だ。

この設計領域を **ハーネスエンジニアリング（Harness Engineering）** と呼ぶ。

---

## 結論を先に

ハーネスエンジニアリングとは、**AIエージェントが動作する実行環境そのものを設計・制御する技術**だ。

モデルの「外側」を作る作業と言ってもいい。

```
ハーネス（囲い）の中で
  ↓ 情報を制御する（何を見せるか）
  ↓ 行動を制御する（何をさせるか）
  ↓ 結果を評価する（何が達成されたかを判定する）
```

ハーネスエンジニアリングの主な実装手段は次のとおりだ。

| 手段 | 役割 |
| :--- | :--- |
| CLAUDE.md / AGENTS.md | エージェントへの静的な指示・文脈注入 |
| Hooks | ライフサイクルイベントへのスクリプト介入 |
| 権限モデル | ツール実行の許可・拒否・確認 |
| ツールサーフェス | エージェントに公開するツールの範囲 |
| エージェントループ設計 | いつ・どう繰り返すかの制御 |

> 2026年に入り、企業がAIエージェントを本番導入した結果、「モデルを賢くすること」より「囲いを正しく作ること」の方が難しいという認識が業界で共有されはじめた。

---

## ハーネスとは何か

「ハーネス」という言葉は、もともとソフトウェアテストの文脈で使われていた。テスト対象コードを制御された環境で動かすための「テストハーネス」だ。

AIエージェントに対して使われる場合は、意味が広がっている。

**モデルが動作する環境全体 ── 何を見られるか、何ができるか、何を返すか ── を制御するシステム**のことを指す。

たとえば Claude Code を例に取ると、ユーザーが直接触っているのは「モデル」だが、その周囲には次のような構造がある。

```
┌──────────────────────────────────────────────┐
│  ハーネス                                       │
│  ┌─────────────────────────────────────────┐  │
│  │  CLAUDE.md / AGENTS.md                   │  │
│  │  （エージェントへの指示・コンテキスト）          │  │
│  ├─────────────────────────────────────────┤  │
│  │  Hooks                                   │  │
│  │  （PreToolUse / PostToolUse / Stop etc.）│  │
│  ├─────────────────────────────────────────┤  │
│  │  Permissions                             │  │
│  │  （ツール実行ポリシー）                        │  │
│  ├─────────────────────────────────────────┤  │
│  │  Tool Surface                            │  │
│  │  （公開するツールの範囲）                       │  │
│  └─────────────────────────────────────────┘  │
│                    ↕                            │
│           [ モデル / LLM ]                       │
│                    ↕                            │
│  ┌─────────────────────────────────────────┐  │
│  │  Evaluation                              │  │
│  │  （テスト・トレース・Human-in-the-loop）    │  │
│  └─────────────────────────────────────────┘  │
└──────────────────────────────────────────────┘
```

モデルはこのハーネスの中で動く。ハーネスがないと、モデルは「何でも見られて、何でもできる状態」で動くことになる。

---

## ハーネスの3層アーキテクチャ

2026年時点で、ハーネスの実務設計は3つの層に整理されている。

### Layer 1: 情報層（Information Layer）

エージェントが**何を見るか**を制御する層だ。

- どの過去情報がコンテキストに含まれるか
- どのツールが公開されているか（ツールのスキーマも含む）
- CLAUDE.md や AGENTS.md で何を事前に教えるか
- コンテキスト圧縮・フィルタリング

エージェントの推論品質は、ここで決まる部分が大きい。良いコンテキストを作れば、プロンプトを精緻化するよりずっと効果が高い。

### Layer 2: 行動層（Action Layer）

エージェントが**何をするか**を制御する層だ。

```
Plan → Tool Call → Guardrail Check → Parse → Retry or Complete
```

この層の中心はエージェントループの設計だ。何度繰り返すか、どういう条件で止まるか、失敗したらどうするか。

Hooks はこの層に属する。PreToolUse で特定の操作を止めたり、PostToolUse で結果をログに残したりできる。

### Layer 3: 評価層（Evaluation Layer）

**何が達成されたかを判定する**層だ。

- テスト・lint・型チェックによる自動検証
- トレーシング（エージェントが何を見て・何をしたかの記録）
- Human-in-the-loop（人間による確認・承認）

評価層がなければ、エージェントが「やった」と言っても本当にやったかどうか確認できない。

---

## 実装要素①: CLAUDE.md と AGENTS.md

### CLAUDE.md

Claude Code が自動的に読み込む設定ファイルだ。プロジェクトルートに置くことで、セッション開始時にエージェントのコンテキストへ自動注入される。

```markdown
# プロジェクト概要
このプロジェクトは Python 3.11 / FastAPI / PostgreSQL を使用する。

# 開発コンベンション
- テストは pytest を使う
- コードフォーマットは Black
- 型注釈は必須（mypy strict）
- マイグレーションは Alembic で管理する

# 実行手順
- 開発サーバー起動: `docker compose up`
- テスト実行: `pytest`
- マイグレーション適用: `alembic upgrade head`

# 注意事項
- データベースへの直接 DROP は行わない
- 本番環境の設定ファイルは編集しない
- secrets.env は絶対にコミットしない
```

CLAUDE.md に書かれた内容は毎回プロンプトに書かなくて済む。エージェントが「知っておくべきこと」を一元管理する場所だ。

### AGENTS.md

CLAUDE.md がClaude Code 専用なのに対して、AGENTS.md はより広いエージェントツール向けのコンベンションだ。複数のエージェント（Claude Code、Codex など）が同じリポジトリを使う場合に、ツール横断的な指示を置く場所として機能する。

重要な違いは、**CLAUDE.md は指示だが、AGENTS.md はエージェント間の合意**という側面が強いことだ。

```markdown
# AGENTS.md

## エージェント間の役割分担
- architect (Claude Code): タスク設計・レビュー・マージ判断
- backend (Codex): API・DB・テストの実装

## コミュニケーションプロトコル
- タスク完了時: `DONE <task-id> -> architect`
- ブロック時: `BLOCKED <task-id> by <理由>`
- レビュー指摘: `CHANGES <task-id> -> backend`

## 実行してはいけないコマンド
- git push --force
- DROP TABLE / DROP DATABASE
- rm -rf（ワークスペース外）
```

---

## 実装要素②: Hooks

Claude Code の Hooks は、エージェントのライフサイクルイベントにシェルスクリプトや HTTP エンドポイントを差し込む仕組みだ。

### 主なフックイベント（2026年6月時点）

| イベント | タイミング |
| :--- | :--- |
| `PreToolUse` | ツール実行の直前 |
| `PostToolUse` | ツール実行の直後 |
| `PostToolUseFailure` | ツール実行が失敗した直後 |
| `Stop` | エージェントが停止する直前 |
| `SessionStart` | セッション開始時 |
| `UserPromptSubmit` | ユーザーがプロンプトを送信した直後 |
| `SubagentStart / SubagentStop` | サブエージェントの起動・停止 |

### PreToolUse の重要性

**PreToolUse はハーネスにおける最強の防御ラインだ。**

CLAUDE.md に書いた「やってはいけないこと」は、モデルの判断次第で上書きされうる。しかし、PreToolUse を終了コード `2` で終了させると、ツール呼び出しが**無条件に**ブロックされる。指示よりコードが強い。

```bash
#!/bin/bash
# pre_tool_use.sh
# PreToolUse hook: 危険なコマンドをブロックする

TOOL_NAME="$1"
TOOL_INPUT="$2"

if [ "$TOOL_NAME" = "Bash" ]; then
  # git push --force のブロック
  if echo "$TOOL_INPUT" | grep -qE 'git\s+push\s+.*--force'; then
    echo "BLOCKED: git push --force は禁止されています" >&2
    exit 2
  fi

  # rm -rf のブロック
  if echo "$TOOL_INPUT" | grep -qE 'rm\s+-rf\s+/'; then
    echo "BLOCKED: ルートへの rm -rf は禁止されています" >&2
    exit 2
  fi

  # secrets ファイルへのアクセスのブロック
  if echo "$TOOL_INPUT" | grep -qE '\.env\.prod|secrets\.env'; then
    echo "BLOCKED: 本番secrets ファイルへのアクセスは禁止されています" >&2
    exit 2
  fi
fi

exit 0
```

Claude Code の `settings.json` にフックを登録する。

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "bash /path/to/pre_tool_use.sh"
          }
        ]
      }
    ]
  }
}
```

### Stop フックの活用

Stop フックは、エージェントが作業を終えたタイミングで何かを実行したい場合に使う。

```bash
#!/bin/bash
# stop_hook.sh
# エージェント停止時にテストを実行して品質を確認する

echo "=== エージェント停止 → 自動テスト実行 ===" >&2
cd "$PROJECT_ROOT"

# テスト実行
if ! pytest --tb=short -q 2>&1; then
  echo "WARNING: テストが失敗しています" >&2
fi

# 整形チェック
if ! black --check . 2>/dev/null; then
  echo "WARNING: Black 整形が必要なファイルがあります" >&2
fi
```

---

## 実装要素③: 権限モデル

Claude Code の権限モデルは、エージェントが実行できる操作を3段階で制御する。

| 設定 | 動作 |
| :--- | :--- |
| 自動許可（allowlist） | 確認なしで実行 |
| 手動確認（default） | ユーザーに確認を求める |
| ブロック（denylist） | 実行を拒否 |

`settings.json` で細かく設定できる。

```json
{
  "permissions": {
    "allow": [
      "Bash(git status)",
      "Bash(git diff*)",
      "Bash(pytest*)",
      "Bash(black*)",
      "Read(*)"
    ],
    "deny": [
      "Bash(git push --force*)",
      "Bash(rm -rf*)",
      "Bash(curl* --upload*)"
    ]
  }
}
```

**最小権限の原則**がここでも基本だ。エージェントには「今やるべきタスクに必要な権限だけ」を与える。開発時は広め、本番に近い環境では狭める。

---

## 実装パターン①: Ralph Loop

Ralph Loop は、**エージェントを繰り返し実行してゴール条件が満たされるまで自律的に作業させる**パターンだ。

名前の由来はアニメ「シンプソンズ」のキャラクター、Ralph Wiggum だ。無邪気に何度でも同じことを試みる姿から来ている。元々は Geoffrey Huntley 氏が考案したコミュニティパターンで、後に Claude Code の `/goal` コマンドとして公式実装された。

### Ralph Loop の核心的な考え方

通常のエージェントは1回動いて止まる。Ralph Loop は次の考え方で動く。

```
1. ゴール条件（exit condition）を定義する
2. エージェントを1ターン実行する（新規コンテキストで）
3. ゴール条件を確認する（テスト・lint・マーカーファイルなど）
4. 満たされていなければ 2. に戻る
5. 満たされたら終了する
```

重要なのは「**新規コンテキストで**」という部分だ。毎回コンテキストをリセットすることで、長時間実行時の「context rot（コンテキスト汚染）」を防ぐ。状態はファイルシステムや git に永続化し、次のターンでそれを読んで再構築する。

### シェルスクリプトによる最小実装

```bash
#!/usr/bin/env bash
# ralph.sh ── Claude Code を繰り返し実行するループ

GOAL_FILE="GOAL.md"         # ゴール条件を書いたファイル
PROGRESS_FILE="progress.md" # 進捗状態のファイル
MAX_ITERATIONS=20           # 最大繰り返し回数
ITERATION=0

# ゴール達成の判定関数（プロジェクトに合わせてカスタマイズする）
check_goal() {
  # テストが全部通っているか
  pytest --tb=no -q 2>&1 | grep -q "passed" || return 1
  # lint がクリーンか
  ruff check . --quiet 2>&1 | grep -q "^$" || return 1
  return 0
}

while [ $ITERATION -lt $MAX_ITERATIONS ]; do
  ITERATION=$((ITERATION + 1))
  echo "=== Iteration $ITERATION / $MAX_ITERATIONS ==="

  # ゴール達成確認
  if check_goal; then
    echo "✓ ゴール達成。ループを終了します。"
    exit 0
  fi

  # git log と進捗ファイルを読んでコンテキストを再構築させる
  PROMPT="$(cat "$GOAL_FILE")

現在の状態:
$(cat "$PROGRESS_FILE" 2>/dev/null || echo '（進捗なし）')

直近のコミット:
$(git log --oneline -5)

テスト状況:
$(pytest --tb=short -q 2>&1 | tail -20)

上記の状態を踏まえて、ゴールに近づくための次のステップを実行してください。
完了したらその内容を progress.md に追記してください。"

  # Claude Code をヘッドレスモードで1ターン実行
  claude --print "$PROMPT"

  # 短いウェイト（API レート制限への配慮）
  sleep 3
done

echo "最大繰り返し回数に達しました。手動で確認してください。"
exit 1
```

### GOAL.md の例

```markdown
# ゴール条件

以下をすべて満たすこと。

1. `pytest` が全テスト通過する
2. `ruff check .` がエラーなしで通る
3. `black --check .` が整形済みと判定する
4. 認証エンドポイント `/auth/login` と `/auth/logout` が実装されている
5. OpenAPI ドキュメントが更新されている

ゴール達成時は `DONE` とだけ書いた progress.md を作成すること。
```

---

## 実装パターン②: /goal コマンド（公式実装）

`/goal` は Ralph Loop の公式 Claude Code 実装だ。2025年末頃に導入され、シェルスクリプト不要でループを実現できる。

### 基本的な使い方

```
/goal <完了条件>（最大4000文字）
```

```
/goal
認証APIの実装が完了すること。
条件:
- pytest が全テスト通過する
- /auth/login と /auth/logout が実装されている
- 型注釈がすべてついている
- APIドキュメントが更新されている
```

実行すると Claude Code は次のように動く。

```
1. ゴール条件を記憶する
2. 通常通り作業を行う
3. 各ターンの終了時に、専用の軽量モデルがゴール条件を評価する
4. 未達成なら次のターンを開始する
5. 達成されたらゴールをクリアして停止する
```

シェルスクリプトと違い、**ゴール評価はモデルが行う**。コード実行ではなくLLMによる判断だ。これは長所でも短所でもある。コードで機械的に判定できる条件（テスト通過・lint クリア）はスクリプトで判定する方が確実だが、「適切に実装されているか」のような判断はLLMの方が得意だ。

| 特徴 | `/goal` | シェルスクリプト Ralph Loop |
| :--- | :--- | :--- |
| 設定の手間 | ほぼゼロ | スクリプト作成が必要 |
| ゴール評価 | LLMが判断 | コードで機械的に判定可 |
| カスタマイズ | 限られる | 自由 |
| 再現性 | やや低い | 高い |
| 適用範囲 | 定性的な完了条件に向く | 定量的な条件（テスト等）に向く |

---

## 実装パターン③: Supervisor Pattern

**Supervisor Pattern** は、上位のエージェント（Supervisor）が下位のエージェント（Worker）の作業を指示・確認・承認する構造だ。

```
Supervisor (Claude / orchestrator)
  ├─ Worker A (Codex / backend)  ← タスク実装
  ├─ Worker B (agy / reviewer)   ← レビュー
  └─ Worker C (specialist)       ← 特定ドメイン
```

Supervisor の役割は次のとおりだ。

- タスクを定義して Worker に割り当てる
- Worker の成果物を受け取ってレビューする
- 品質基準を満たさなければ差し戻す
- 複数 Worker の作業を統合する

重要なのは、**Supervisor が「判断」を持ち、Worker は「実行」だけを担う**という役割分担だ。Worker が自律的に判断の範囲を広げると、Supervisor の制御が機能しなくなる。

### Phase-gating

Phase-gating は Supervisor Pattern と組み合わせて使われるパターンで、作業フェーズ間に明示的なゲートを設ける。

```
Phase 1: 設計（DESIGN）
  → Gate: アーキテクチャ承認
Phase 2: 実装（IMPLEMENT）
  → Gate: テスト通過・レビュー承認
Phase 3: 統合（INTEGRATE）
  → Gate: E2Eテスト通過
Phase 4: リリース（RELEASE）
  → Gate: 人間による最終確認
```

各ゲートを通過しなければ次のフェーズに進めない。「リリースフェーズに進んでいいのに設計が終わっていない」という状態を構造的に防ぐ。

コスト的に大きい操作（本番デプロイ・データベース変更など）の前には必ず人間承認のゲートを置く。

---

## 実装パターン④: Circuit Breaker

**Circuit Breaker（サーキットブレーカー）** は、エージェントが「ドゥームループ」に陥るのを防ぐパターンだ。

ドゥームループとは、同じ失敗を繰り返し続ける状態だ。エージェントが「なぜ失敗しているか」を理解しないまま同じアプローチを試み続けると、コストと時間だけが消費される。

```
ドゥームループの例:
iteration 1: ファイルAを修正 → テスト失敗
iteration 2: ファイルAを修正（同じアプローチ）→ テスト失敗
iteration 3: ファイルAを修正（同じアプローチ）→ テスト失敗
...（繰り返す）
```

### Circuit Breaker の実装

```bash
#!/usr/bin/env bash
# circuit_breaker.sh

FAILURE_LOG="/tmp/agent_failures.log"
MAX_CONSECUTIVE_FAILURES=3
SAME_FILE_EDIT_LIMIT=5

# 同一ファイルへの連続編集回数をカウント
check_edit_count() {
  local file="$1"
  local count
  count=$(grep -c "EDIT:$file" "$FAILURE_LOG" 2>/dev/null || echo 0)
  if [ "$count" -ge "$SAME_FILE_EDIT_LIMIT" ]; then
    echo "CIRCUIT_OPEN: $file への編集が $count 回に達しました" >&2
    echo "異なるアプローチを検討してください。人間の判断が必要かもしれません。" >&2
    exit 2  # PreToolUse hook としてブロック
  fi
  echo "EDIT:$file" >> "$FAILURE_LOG"
}

# 連続失敗回数をカウント
check_failure_count() {
  local count
  count=$(grep -c "FAIL:" "$FAILURE_LOG" 2>/dev/null || echo 0)
  if [ "$count" -ge "$MAX_CONSECUTIVE_FAILURES" ]; then
    echo "CIRCUIT_OPEN: $count 回連続で失敗しました" >&2
    echo "BLOCKED: 手動確認が必要です" >&2
    exit 2
  fi
}
```

Circuit Breaker が発動したら、エージェントはタスクを `BLOCKED` として人間に戻す。「頑張り続けること」よりも「詰まったと報告すること」の方が設計として正しい。

---

## ハーネス設計の原則

ここまで個別の実装手段を見てきた。最後に設計の原則を整理する。

### 1. 指示よりコードを信頼する

「やってはいけない」を CLAUDE.md に書くだけでは不十分だ。PreToolUse hook で終了コード `2` を返す方が確実だ。指示はモデルの判断で上書きされうるが、コードは上書きされない。

### 2. 最小権限で始める

エージェントに最初から広い権限を与えない。「今のタスクに必要な権限」だけを与え、必要に応じて広げる。後から狭めるより、最初から狭い方が安全だ。

### 3. ループは有限にする

Ralph Loop も自動起動スクリプトも、必ず最大回数・最大時間を設ける。「エージェントが自律的に動き続ける」状態は、問題が起きたときに発見が遅れる。

### 4. 評価はモデルと独立させる

「テストが通ったか」の判断をモデル自身にさせない。テスト実行・lint・型チェックは独立したプロセスで行う。「成功した」という報告よりも、実際に成功しているかの確認が必要だ。

### 5. 人間が止められるようにする

どんな自動化でも、人間がいつでも止められる仕組みを用意する。完全自動化が目標でも、非常停止手段がなければ問題発生時の被害が拡大する。

---

## まとめ

| ポイント | 内容 |
| :--- | :--- |
| **ハーネスとは** | エージェントの情報・行動・評価を制御する実行環境の設計 |
| **3層構造** | 情報層（何を見る）・行動層（何をする）・評価層（何が達成されたか） |
| **CLAUDE.md** | セッション開始時に自動注入される静的コンテキスト |
| **Hooks** | PreToolUse が最強の防御ライン。コードはプロンプトより強い |
| **Ralph Loop** | コンテキストをリセットしながらゴール達成まで繰り返すパターン |
| **/goal** | Ralph Loop の公式実装。LLMがゴール達成を判断する |
| **Supervisor Pattern** | 判断を持つ上位エージェントが実行する下位エージェントを管理 |
| **Circuit Breaker** | ドゥームループを検出して自動停止し、人間に戻す |

ハーネスエンジニアリングは「エージェントに良いコードを書かせるための呪文集」ではない。

**「エージェントが何をしても、意図した範囲を超えられない構造を作ること」** だ。

モデルが賢くなるほど、この構造の重要性は増す。なぜなら賢いモデルほど、意図していない方法で目標を達成しようとする能力も高くなるからだ。その問題については続篇で詳しく扱う。

---

## 参考

- [Skill Issue: Harness Engineering for Coding Agents](https://www.humanlayer.dev/blog/skill-issue-harness-engineering-for-coding-agents) — HumanLayer による実践的な解説
- [Agent Harness Engineering — The Rise of the AI Control Plane](https://medium.com/@adnanmasood/agent-harness-engineering-the-rise-of-the-ai-control-plane-938ead884b1d) — Adnan Masood によるコントロールプレーンとしてのハーネス論
- [AddyOsmani.com — Agent Harness Engineering](https://addyosmani.com/blog/agent-harness-engineering/) — Addy Osmani によるハーネスエンジニアリング解説
- [The Complete Claude Code Harness Engineering Guide](https://dev.to/shipwithaiio/the-complete-claude-code-harness-engineering-guide-5-layers-8-deep-dives-3d4j) — DEV Community での5層・8詳解ガイド
- [Claude Code Architecture Explained: Six Harness Layers](https://mer.vin/2026/05/claude-code-architecture-explained-six-harness-layers-beyond-the-llm/) — Mervin Praison によるClaudeハーネス6層解説
- [Ralph Wiggum Loop and /goal in Claude Code](https://theaiarchitects.com/blog/claude-code-ralph-loop) — /goal コマンドとRalph Loopの実践解説
- [GitHub: snarktank/ralph](https://github.com/snarktank/ralph) — Ralph の元実装リポジトリ
- [GitHub: frankbria/ralph-claude-code](https://github.com/frankbria/ralph-claude-code) — Claude Code 向けのRalph実装
- [Claude Code Hooks reference](https://docs.anthropic.com/en/docs/claude-code/hooks) — Claude Code 公式Hooksドキュメント
- [GitHub: ai-boost/awesome-harness-engineering](https://github.com/ai-boost/awesome-harness-engineering) — ハーネスエンジニアリングのAwesomeリスト
