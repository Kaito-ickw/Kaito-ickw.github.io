---
layout: post
title: "マルチエージェント開発における非対称な引き継ぎ問題 ── Claude→Codexが止まる理由と解消パターン6選"
subtitle: メッセージ配信・プロセス起動・実行ポリシーの3層を分けて設計する
categories: 開発
tags: ["マルチエージェント", "Claude Code", "Codex", "agmsg", "自動化", "AI開発"]
lang: ja
ref: multi-agent-asymmetric-handoff
---

AIエージェントを複数組み合わせて開発を進めると、ある非対称な問題にぶつかる。

一方向はうまく動く。Codexが実装を終えてメッセージを送ると、待機中のClaudeが検知してレビューを始める。しかし逆方向はそうではない。ClaudeがレビューしてCodexへ修正依頼を送っても、すでに停止したCodexは自分でそれを拾いに来ない。

この記事では、その非対称性の原因を整理し、解消パターン6案を比較する。

---

## 現在のマルチエージェント構成

前提となる構成を説明する。

```
Claude Code  ── orchestrator / architect
             ── 設計、タスク分割、レビュー、mainへの統合
             ── agmsg identity: team=ailedger / name=architect
             ── monitor モードでメッセージ待受

Codex        ── backend implementer
             ── API・DB・テストの連続実装
             ── agmsg identity: team=ailedger / name=backend
             ── agmsg配信モードは turn または off

agy/Gemini   ── ワンショットの機械レビュー（常駐しない）
```

**agmsg** は、SQLiteを使ったエージェント間メッセージング基盤だ。同一devcontainer内の共有SQLiteを使い、ネットワークや常駐daemonを必要としない。メッセージ形式は次のとおり。

```text
START   <task-id> <説明>
DONE    <task-id> -> <相手> <内容>
CHANGES <task-id> -> backend <指摘>
APPROVED <task-id> -> orchestrator マージ可
BLOCKED <task-id> by <理由>
LOWQUOTA <name> <残り目安>
```

Git運用はエージェントごとの専用worktree/branchで行う。architectがタスクを発行し、Codexが実装して`DONE`を送る。Claudeがレビューしてmergeまたは`CHANGES`を返す。

---

## 成功している片方向フロー

現在、次のフローは問題なく動いている。

```text
Codexが実装完了
  → agmsg: DONE task-001 -> architect 実装完了
  → monitor中のClaudeが検知
  → Claude: git diff で差分確認
  → Claude: レビュー・テスト
  → merge または CHANGES送信
```

Claudeは`monitor`モードで待機しており、agmsgのinboxに新着が来ると自動的に処理を開始できる。これが片方向フローが機能する理由だ。

---

## Claude→Codexで止まる理由

逆方向のフローは詰まる。

```text
Claudeがレビュー完了
  → agmsg: CHANGES task-001 -> backend 〇〇を修正してください
  → Codexは前ターン終了後に停止している
  → 停止中のCodexは自分でinboxを監視できない
  → 新しいCodexターンが開始されない
  → メッセージがinboxで滞留する
```

「なぜCodexは自分でメッセージを拾えないのか」という疑問が自然に出る。次の節でその理由を整理する。

---

## `turn`モードと`monitor`モードの違い

Claudeの`monitor`モードは、agmsgのinboxを継続的に監視し、新着メッセージが届いたときに処理を開始する仕組みだ。

Codexの`turn`モードは**これとは異なる**。`turn`モードが提供するのは次の機能だ。

- Codexが活動中のターン終端で、stop hookがinboxを確認する
- 確認時にメッセージがあれば、同一ターン内で処理できる

`turn`モードが提供**しない**のは次のことだ。

- ターン終了後の常時監視
- 新着を待つdaemon
- 停止中のCodexプロセスを外部から起動する機能
- ClaudeからCodexの新規ターンを直接開始する機構

つまり、Codexのターンが終わった時点でその実行コンテキストは消える。agmsgにメッセージが届いても、それを受け取るプロセスが存在しない。

---

## 通信とプロセス起動は別問題

ここが設計の核心だ。問題を3層に分けて考える必要がある。

```
Layer 1: Message transport
  → agmsgがメッセージを届ける
  → 現在、この層は機能している

Layer 2: Wake-up mechanism
  → 停止中のCodexプロセスを起動する
  → 現在、この層が欠けている

Layer 3: Execution policy
  → 起動後、何をどの権限で実行してよいか判断する
  → 完全自動化では必ず設計が必要
```

**agmsgが解決するのは主にLayer 1**だ。  
**今回不足しているのはLayer 2**だ。  
完全自動化を目指すなら**Layer 3も設計しなければならない**。

この3層を混同したまま実装しようとすると、「agmsgでメッセージを送ればCodexが動くはず」という誤解が生まれ、予期しない穴が空く。

---

## 解消パターン6案

### パターン1: 人間による起動

ClaudeのCHANGES/TASK通知を人間が確認し、手動でCodexを再開する。

```text
Claude → agmsg CHANGES
  → 人間がinboxを確認（定期的に手動チェック）
  → 人間がCodexを起動
  → Codexが実装・修正
```

**評価:**

| 観点 | 評価 |
| :--- | :--- |
| 自動化レベル | 最低（人間待ち） |
| 実装コスト | ほぼゼロ |
| 誤起動リスク | 最低 |
| 二重起動リスク | 人間が管理するため低い |
| 夜間・離席中 | 止まる |
| 小規模個人開発での合理性 | **高い** |

完全自動化の必要がない規模では、これが最もシンプルかつ安全だ。「自動化できていないこと」をデメリットとして捉えすぎないようにしたい。朝起きてinboxを確認してから起動するワークフローは、予期しない暴走を防ぐという意味で積極的に選ぶ理由がある。

---

### パターン2: Codexの時間制限付きポーリング

Codexのターンを終了させず、一定間隔でinboxを確認し続ける。

```bash
# Codexのターン内で実行
MAX_WAIT=1800  # 30分
INTERVAL=300   # 5分
elapsed=0

while [ $elapsed -lt $MAX_WAIT ]; do
  msg="$(agmsg inbox --name backend --team ailedger 2>/dev/null)"
  if echo "$msg" | grep -qE '^(CHANGES|TASK|APPROVED)'; then
    echo "メッセージ受信: $msg"
    break
  fi
  sleep $INTERVAL
  elapsed=$((elapsed + INTERVAL))
done
```

**評価:**

| 観点 | 評価 |
| :--- | :--- |
| 自動化レベル | 中（ターン内で完結） |
| 実装コスト | 低い |
| 追加基盤 | 不要 |
| ターン占有 | **する**（ターンを使い続ける） |
| セッション切断耐性 | 弱い（切断で失敗） |
| 長時間待機 | 不向き（コスト・リスクが増加） |

「sleep中にモデルの課金が進むか」については、実行環境やプロバイダによって異なる。断定できないため、長時間のポーリングを計画する場合は自分の環境で確認すること。

短いレビュー待ち（10〜15分以内）に限れば、追加基盤なしで機能する。ただしターンを占有し続けるため、並行タスクとの兼ね合いで計画的に使う必要がある。

---

### パターン3: モデル非依存の軽量watcher

モデルの外側で動くbashスクリプトがagmsgを監視し、人間に通知する。

```bash
#!/usr/bin/env bash
# watcher.sh ── agmsg inboxを監視して通知する（Codexは起動しない）

TEAM="ailedger"
NAME="backend"
INTERVAL=30

while true; do
  msg="$(agmsg inbox --name "$NAME" --team "$TEAM" 2>/dev/null)"
  if [ -n "$msg" ]; then
    task_id="$(echo "$msg" | awk '{print $2}')"
    echo "[watcher] 新着: $msg"
    echo "[watcher] Codexを起動するには:"
    echo "  codex --task-id $task_id"
    # 必要に応じてOS通知・Slack通知などを追加
    # notify-send "agmsg新着" "$msg" 2>/dev/null
  fi
  sleep $INTERVAL
done
```

このwatcherは**Codexを自分では起動しない**。人間への通知と起動コマンドの表示に留める。

**評価:**

| 観点 | 評価 |
| :--- | :--- |
| 自動化レベル | 半自動（通知のみ） |
| 実装コスト | 低い |
| モデル待機コスト | なし |
| セッション切断耐性 | 強い（shellが動き続ける） |
| agmsgとの相性 | 良い（提供CLIのみ使用） |
| 安全性 | 高い（Codexは人間が起動） |

重要な制約として、**agmsgが管理するSQLiteを直接読み書きしてはいけない**。提供されているCLIスクリプトだけを使うことでagmsgの整合性を守る。

現行構成への追加が最小で、モデルコストが発生せず、人間が最終確認を行えるため、**最初に導入する解決策として最も現実的**だ。

---

### パターン4: dispatcherによるCodex自動起動

外部dispatcherが新着TASK/CHANGESを検知し、Codex CLIをワンショット起動する。

```text
Claude → agmsg TASK/CHANGES
  → dispatcherが30秒間隔でinboxを確認
  → task-idを抽出してallowlist検証
  → task-id単位のロックを取得
  → 対象worktreeの存在確認
  → Codex CLIをワンショット起動
  → Codexが実装・検証
  → agmsg DONE / BLOCKED
  → ロックを解放・ログを記録
  → プロセス終了
```

疑似コードで安全要件を示す。

```bash
#!/usr/bin/env bash
# dispatcher.sh（疑似コード ── 本番利用前に安全設計を完成させること）

ALLOWED_REPOS=("/workspace")
ALLOWED_SENDERS=("architect")
LOCK_DIR="/tmp/agmsg-locks"
MAX_RETRY=3
MAX_RUNTIME=3600  # 60分

mkdir -p "$LOCK_DIR"

while true; do
  msg="$(agmsg inbox --name backend --team ailedger 2>/dev/null)"

  if [ -z "$msg" ]; then
    sleep 30
    continue
  fi

  # メッセージ型の検証（TASK / CHANGES のみ対象）
  msg_type="$(echo "$msg" | awk '{print $1}')"
  if ! echo "$msg_type" | grep -qE '^(TASK|CHANGES)$'; then
    sleep 30
    continue
  fi

  # 送信元の検証（architectのみ許可）
  sender="$(echo "$msg" | grep -oP 'from=\K\S+')"
  if [ "$sender" != "architect" ]; then
    echo "[dispatcher] 不正な送信元: $sender"
    sleep 30
    continue
  fi

  # task-idの抽出と検証（英数字・ハイフンのみ許可）
  task_id="$(echo "$msg" | awk '{print $2}' | grep -E '^[a-zA-Z0-9-]+$')"
  if [ -z "$task_id" ]; then
    echo "[dispatcher] task-id検証失敗"
    sleep 30
    continue
  fi

  # 二重起動防止（task-idロック）
  lock_file="$LOCK_DIR/$task_id.lock"
  if [ -f "$lock_file" ]; then
    echo "[dispatcher] $task_id はすでに実行中"
    sleep 30
    continue
  fi

  # LOWQUOTA確認
  quota="$(agmsg inbox --name backend --team ailedger --type LOWQUOTA 2>/dev/null)"
  if [ -n "$quota" ]; then
    echo "[dispatcher] クォータ不足のため停止: $quota"
    break
  fi

  # worktreeのallowlist検証
  worktree="$(echo "$msg" | grep -oP 'worktree=\K\S+')"
  valid_repo=false
  for allowed in "${ALLOWED_REPOS[@]}"; do
    if [[ "$worktree" == "$allowed"* ]]; then
      valid_repo=true
      break
    fi
  done
  if [ "$valid_repo" = false ]; then
    echo "[dispatcher] 許可されていないworktree: $worktree"
    agmsg send --name architect --team ailedger "BLOCKED $task_id by 許可されていないworktree"
    sleep 30
    continue
  fi

  # ロック取得 → 起動 → 解放
  touch "$lock_file"
  echo "[dispatcher] $task_id 起動 (worktree: $worktree)"

  # メッセージ本文をそのままshellへ渡さない
  # eval不使用、文字列展開不使用
  timeout "$MAX_RUNTIME" codex \
    --worktree "$worktree" \
    --task-id "$task_id" \
    --no-auto-approve-destructive \
    2>&1 | tee "/tmp/agmsg-logs/$task_id.log"

  exit_code=$?
  rm -f "$lock_file"

  if [ $exit_code -ne 0 ]; then
    agmsg send --name architect --team ailedger \
      "BLOCKED $task_id by Codex異常終了 (exit=$exit_code)"
  fi

  sleep 30
done
```

**必須の安全要件（dispatcherを実装するなら全て実装すること）:**

- 同じtask-idの二重起動防止（ファイルロック等）
- 同一Codexプロバイダの並列起動防止
- 最大実行時間の強制終了
- 最大再試行回数の制限
- 許可されたworktreeのみ対象
- 許可された送信元（architectのみ）
- `TASK`と`CHANGES`以外では起動しない
- メッセージ本文を`eval`しない・shellコマンドとして直接実行しない
- task-id/branch/worktreeをallowlist検証する
- destructiveなコマンドを自動承認しない
- LOWQUOTA受信時は停止する
- ログとtask-idを対応づける
- 異常終了時に`BLOCKED`を返す
- ループ検出・防止
- 人間が停止できるkill switch（PIDファイル、またはシグナル）

**評価:**

| 観点 | 評価 |
| :--- | :--- |
| 自動化レベル | 高 |
| 実装コスト | **高い**（安全要件が多い） |
| 誤起動リスク | 設計次第で低減可能 |
| 二重起動リスク | ロックで防止 |
| セキュリティ | 設計が重要 |
| 監査性 | ログ必須 |

---

### パターン5: tmux等でCodexセッションを維持する方式

tmuxのような端末多重化ツールでCodexセッションを生かし続け、外部watcherがキー入力を注入する。

```bash
# 概念的な例（実運用向けではない）
tmux send-keys -t codex-session "agmsg inbox確認中..." Enter
```

**評価:**

| 観点 | 評価 |
| :--- | :--- |
| 会話コンテキスト維持 | 可能性はあるが不安定 |
| 入力注入の信頼性 | **低い**（CLI UIの変更に依存） |
| セッション状態への依存 | 強い |
| unattended運用の安全性 | 懸念が大きい |
| CLI UI変更の影響 | 受けやすい |

tmuxによるキー注入は、CLIのプロンプト状態を正確に把握できないと正しく動かない。Codex CLIのUI変更ひとつでスクリプトが壊れる。完全自動化の初期案として構造を考える参考にはなるが、本番運用として採用する理由は少ない。

---

### パターン6: GitHub / CIをジョブキューとして使う方式

GitHub Issue・PRコメント・label・`workflow_dispatch`などをトリガーにして、Codexをrunnerで起動する。

```yaml
# .github/workflows/codex-dispatch.yml
on:
  workflow_dispatch:
    inputs:
      task_id:
        description: 'task-id'
        required: true
jobs:
  run-codex:
    runs-on: self-hosted
    steps:
      - name: Run Codex for task
        run: codex --task-id ${{ github.event.inputs.task_id }}
```

**評価:**

| 観点 | 評価 |
| :--- | :--- |
| 監査ログ | **充実**（GitHub履歴に残る） |
| リポジトリ外からの起動 | 可能 |
| 必要インフラ | GitHub Actions runner（self-hosted or GitHub hosted） |
| 秘密情報管理 | GitHub Secrets経由で管理可能 |
| 現行ローカル優先方針との相性 | 低い |
| agmsgとの二重正本化リスク | **あり**（状態管理が分散する） |

現在の構成はローカル優先・低コストを優先しており、agmsgとGitHub状態の二重正本化は避けたい。大規模チームや外部からのトリガーが必要になった場合には有力な選択肢だが、個人・小規模開発の初期フェーズでは導入コストが見合わない場面が多い。

---

## 比較表

| 方式 | 自動化 | 実装コスト | モデル待機コスト | 誤起動リスク | 二重起動リスク | セッション切断耐性 | 監査性 | agmsg相性 | 小規模適合 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1. 人間による起動 | ✗ | 最小 | なし | 最低 | 最低 | 強 | 低 | ◎ | **◎** |
| 2. Codexポーリング | △ | 低 | あり | 低 | 低 | 弱 | 低 | ◎ | △ |
| 3. 軽量watcher | △ | 低 | なし | 低 | 低 | 強 | 中 | ◎ | **○** |
| 4. dispatcher自動起動 | ◎ | **高** | なし | 設計次第 | ロックで低減 | 強 | 高 | ○ | △ |
| 5. tmuxセッション維持 | ○ | 中 | あり | 中 | 中 | 弱 | 低 | △ | ✗ |
| 6. GitHub/CI | ◎ | 高 | なし | 低 | 低 | 強 | **高** | △ | ✗ |

---

## 推奨する段階的導入

最初から完全自動化を目指すべきではない。誤起動・二重起動・暴走の被害を最小化しながら、段階的に自動化の範囲を広げる。

### Phase A: 半自動通知（今すぐ導入できる）

軽量watcherがTASK/CHANGESを検知し、人間に通知する。Codexの起動は人間が行う。

```bash
# watcher.sh（最小構成）
while true; do
  msg="$(agmsg inbox --name backend --team ailedger 2>/dev/null)"
  [ -n "$msg" ] && echo "[$(date)] 新着: $msg"
  sleep 30
done
```

この段階で得られること：

- Codex停止中でもメッセージ滞留を即座に把握できる
- モデルコストがかからない
- 起動の判断は常に人間にある

### Phase B: 承認付き起動

watcherが起動候補を表示し、人間の1回承認でCodexをワンショット起動する。

```bash
# 承認プロンプト付き起動
read -p "Codexを起動しますか？ [y/N] " confirm
if [ "$confirm" = "y" ]; then
  touch "$LOCK_DIR/$task_id.lock"
  timeout 3600 codex --task-id "$task_id" --worktree "$worktree"
  rm -f "$LOCK_DIR/$task_id.lock"
fi
```

この段階で追加すること：

- task-idロック（二重起動防止）
- タイムアウト（最大実行時間）
- ログ記録（task-id対応）

### Phase C: 制限付き自動起動

安定したユースケースに限って自動化する。

条件：

- architectからのメッセージのみ対象
- 許可済みworktreeでのみ起動
- 1タスク1プロセス（ロック必須）
- 修正回数に上限を設ける（無限ループ防止）
- 設計判断が必要なメッセージは自動的に`BLOCKED`として返す

**完全自動化を最初から採用しない理由：**

現時点では、Codex CLIのインターフェースや挙動の細部について、自動判断に必要な仕様が十分に確定していない部分がある。また、dispatcherが誤って同一タスクに対してCodexを連続起動した場合、同一worktreeへの競合コミットが発生しうる。段階的な導入により、各フェーズで問題を早期に検出し、安全に進められる。

---

## dispatcher設計時の安全要件

dispatcherが実際に使えるものになるには、自由文のメッセージをそのまま処理するだけでは不十分だ。

**自由文だけでdispatcherを動かす危険性：**

```text
# agmsgで送られたこのメッセージをdispatcherがそのままshellで処理すると...
CHANGES task-001 -> backend ; rm -rf /workspace

# eval や $() 経由で展開した場合、意図しないコマンドが実行される
```

このため、構造化メッセージフォーマットへの移行を検討する。

```json
{
  "type": "TASK",
  "task_id": "MIG-001",
  "from": "architect",
  "to": "backend",
  "repo": "/workspace",
  "worktree": "/workspace/.worktrees/alembic",
  "branch": "feat/alembic",
  "action": "implement",
  "max_runtime_minutes": 60,
  "requires_human_approval": true
}
```

ただし、現行agmsgは自由文中心の設計だ。互換性を壊さない移行案として、既存メッセージに`TASKJSON`プレフィックスをつける方式がある。

```text
# 通常の自由文（既存の形式 ── 変更なし）
TASK task-002 -> backend DBマイグレーション実装

# dispatcher向けの構造化メッセージ（新形式）
TASKJSON {"type":"TASK","task_id":"MIG-001","from":"architect",...}
```

この方式なら：

- 既存の自由文メッセージはそのまま動く
- dispatcherは`TASKJSON`プレフィックスのものだけをパースする
- 自由文の`TASK`に対してdispatcherは動かない（安全）
- 段階的に構造化対応を進められる

---

## このプロジェクトへの推奨構成

現在の「AIネイティブなLedgerシステム」開発における推奨は次のとおりだ。

**今すぐやること:**

1. **Codexを長時間sleepさせない**  
   ターン内でのポーリングは短時間（10〜15分以内）に限定する

2. **モデル非依存の軽量watcherを導入する**（Phase A）  
   agmsgのCLIのみを使って監視し、人間に通知する  
   SQLiteを直接読まない・agmsg CLIだけを使う

3. **最初は人間承認付きで運用する**  
   watcherが通知 → 人間が確認 → 手動でCodexを起動  
   この運用で「どの状況でCodexを起動したいか」を具体的に把握する

**安定したら進めること:**

4. **task-id単位の二重起動防止を導入する**（Phase B）  
   lockファイルでシンプルに実装できる

5. **制限付きワンショット自動起動へ進む**（Phase C）  
   `TASKJSON`形式の構造化メッセージのみ対象  
   worktree allowlist・送信元検証・タイムアウト・LOWQUOTA停止を揃えてから

**継続的に守ること:**

6. **常駐Codexを2つ並走させない**  
   同一プロバイダで2インスタンス起動するとレート消費が倍になる

7. **設計判断は自動処理せずarchitectへ戻す**  
   `BLOCKED`を使って人間の判断に委ねる  
   「Codexが迷ったまま実装し続ける」よりコストが低い

---

## まとめ

マルチエージェント開発における非対称な引き継ぎ問題は、「メッセージを届ける仕組み」と「停止中のプロセスを起動する仕組み」が別物であることを認識することで整理できる。

agmsgはLayer 1（メッセージ配信）を担うが、Layer 2（プロセス起動）とLayer 3（実行ポリシー）は別途設計が必要だ。

完全自動化は最終的なゴールとして有効だが、段階的に導入しないと「誰も見ていない間にCodexが意図しない実装を繰り返す」リスクが生まれる。

まず軽量watcherで人間が状況を把握できる状態を作り、そこから承認フロー・ロック・タイムアウトを加えて、確認が取れてから自動起動へ進む。この順序が小規模個人開発においては合理的だと思っている。

---

## 付録: agmsgを使う際の注意点

- agmsgが管理するSQLiteは**直接読み書きしない**
- 提供されているCLIスクリプトだけを使う
- メッセージ本文を`eval`しない
- シェル文字列として直接実行しない
- task-id / branch / worktreeはallowlistで検証する
- dispatcherを実装する場合は、まずPhase AとBで実運用の感覚を掴んでからにする

---

## 参考情報

### agmsg

- [agmsg — Cross-agent messaging for CLI AI agents](https://agmsg.cc/) — 公式サイト。インストール手順・モード一覧・クイックスタート
- [GitHub: fujibee/agmsg](https://github.com/fujibee/agmsg) — ソースコード・セットアップスクリプト・issueトラッカー
- [I built agmsg so Claude Code and Codex could stop using me as a copy-paste relay](https://dev.to/fujibee/i-built-agmsg-so-claude-code-and-codex-could-stop-using-me-as-a-copy-paste-relay-m42) — 作者によるDEV Communityの解説記事。設計の背景とユースケースが詳しい

### Claude Code

- [Hooks reference — Claude Code Docs](https://docs.anthropic.com/en/docs/claude-code/hooks) — Stop / SessionStart / PostToolUse など各hookのイベント仕様と設定方法

### Codex CLI

- [Codex CLI — OpenAI Developers](https://developers.openai.com/codex/cli) — Codex CLIの概要・インストール
- [Features — Codex CLI](https://developers.openai.com/codex/cli/features) — hookやエージェントモードの機能一覧
- [Command line options — Codex CLI](https://developers.openai.com/codex/cli/reference) — CLIオプションリファレンス
