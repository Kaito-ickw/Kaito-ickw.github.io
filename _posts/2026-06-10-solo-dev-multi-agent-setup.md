---
layout: post
title: "1人開発でマルチエージェント体制を作る方法"
subtitle: 役割分担・通信設計・Git worktreeで構成する実践パターン
categories: AI開発
tags: ["マルチエージェント", "Claude Code", "Codex", "agmsg", "AIネイティブ開発", "コーディングエージェント", "自動化"]
lang: ja
ref: solo-dev-multi-agent-setup
---

「マルチエージェント」という言葉を聞くと、大人数のチームが巨大なシステムを動かしているイメージが先行する。しかし1人開発でも、エージェントを複数動かす設計は成立する。むしろ1人だからこそ、役割分担を明確にして自分の判断コストを下げる意義がある。

この記事では、1人開発でマルチエージェント体制を組む際の設計の考え方と、実際の構成パターンを整理する。

---

## 結論を先に

1人開発でのマルチエージェント体制は、次の3要素で成り立つ。

1. **役割の分離** ── オーケストレーター（設計・レビュー・統合）と実装担当を分ける
2. **通信の設計** ── エージェント間のメッセージパスを定義する
3. **自分の立ち位置** ── 人間はPMとして動く。コードを書かず、承認と判断をする

完全な自動化は最終形ではあるが、最初から目指す必要はない。まずは「Claude + Codex + 自分」の3者分業から始めるのが現実的だ。

---

## なぜ1人開発でマルチエージェントが有効か

1人でAIエージェントを使うとき、最初は「Claude Codeに全部任せる」スタイルになりやすい。これは悪くない。しかしある規模を超えると限界が出る。

- コンテキストが長くなり、エージェントの出力品質が落ち始める
- 設計とコーディングが同じエージェントで混在し、役割が曖昧になる
- 自分が「何が進んでいるか」を把握しにくくなる

マルチエージェントにする最大の理由はコンテキストの分離だ。オーケストレーターは「何が済んで・何が残っているか」を把握し続ける。実装担当はタスクが終わったらセッションを終了し、次のタスクは白紙で始める。この構造だけで、長時間開発のコンテキスト劣化（context rot）を大幅に減らせる。

詳細は[エージェントを長く自律動作させるためのコンテキスト設計]({% post_url 2026-06-07-agent-context-management-2026 %})で扱っている。

---

## 役割設計

最小構成で始めるなら、役割は2つで十分だ。

```
orchestrator (Claude Code)
  役割: タスク定義・設計レビュー・mainへの統合判断
  コンテキスト: 長く維持する

implementer (Codex)
  役割: API・DB・テストの実装
  コンテキスト: タスクごとにリセットする
```

orchestratorは「何をやるか」を決め、implementerは「どうやるか」を実行する。この分離が機能していれば、orchestratorが長い会話履歴を持っていても、implementerのコンテキストは常に軽い状態を保てる。

1人開発に加えて機械レビューが欲しい場合は、ワンショットのreviewerを追加する選択肢もある。常駐させる必要はなく、diff を渡して1回だけ実行する用途で十分だ。

---

## 通信の設計

エージェントを複数動かす場合、「何をやって・何が終わったか」の情報をどこで共有するかを決めておく必要がある。

最もシンプルな方法はファイルベースだ。`tasks.md` にタスク一覧を置き、各エージェントが読み書きする。追加インフラが不要で、git で履歴も残る。

```markdown
# tasks.md

## 進行中
- [ ] task-001: /auth/login エンドポイントの実装 [backend]

## 完了
- [x] task-000: DB スキーマ設計 [architect]
```

専用のメッセージングが必要になったら **agmsg** を使う選択肢がある。SQLiteを使ったエージェント間メッセージング基盤で、ネットワーク不要でdevcontainer内で完結する。メッセージは次の形式で送受信する。

```text
DONE    task-001 -> architect 実装完了、テスト通過
CHANGES task-001 -> backend  エラーハンドリングを追加してください
BLOCKED task-001 by         DB接続の設定値が不明
```

ただし、agmsgを使い始めると「ClaudeからのCHANGESをCodexがどう受け取るか」という非対称な引き継ぎ問題が出る。この問題と解消パターンは[Claude と Codex のマルチエージェント引き継ぎ問題と解消パターン]({% post_url 2026-06-07-multi-agent-asymmetric-handoff %})で詳しく整理した。

最初はファイルベースで始め、ボトルネックが出てきたらagmsgへ移行するのが無駄が少ない。

---

## Git worktreeの設計

複数のエージェントが同じリポジトリで並行作業するとき、同一ブランチで作業させると競合が発生する。これを防ぐにはworktreeを使う。

```bash
# 各エージェント専用のworktreeを作る
git worktree add .worktrees/backend feat/auth-api
git worktree add .worktrees/review  review/auth-api
```

構造のイメージはこうなる。

```
.
├── （メインworktree: main / orchestratorの作業場）
└── .worktrees/
    ├── backend/   ← Codexが実装する場所
    └── review/    ← レビュー用（必要なら）
```

タスクが完了したら、orchestratorがdiffを確認してmainにマージする。worktreeはタスクごとに作り直してもいいし、役割に固定して使い続けてもいい。

worktreeのメリットはもう一つある。エージェントの作業範囲を物理的に分離できるため、「Codexがmainのファイルを誤って上書きする」という事故が起きにくい。ハーネス設計の観点では、ファイルシステムレベルでの分離は強力な安全装置だ。

---

## 人間の役割: PMとして動く

この体制で1人開発者が担う役割は、コードを書くことではなくなる。

- タスクを定義してorchestrator（Claude）に渡す
- orchestratorが出したCHANGESやBLOCKEDに判断を下す
- 実装が完了したらdiffを確認してmergeする
- agmsgのinboxを定期的に確認する

実際の1日の流れはこうなる。

```
朝:
  tasks.md を確認
  → orchestratorに「今日やること」を伝える
  → orchestratorがタスクを分割してCodexに割り当てる

作業中:
  orchestratorのCHANGES/BLOCKEDが来たら判断する
  Codexがタスクを完了したらdiffを確認

夜:
  orchestratorにセッションを終了させる前にsummaryを書かせる
  → 翌朝のコンテキスト再構築に使う
```

この運用で最も重要なのは、BLOCKEDを軽く扱うことだ。Codexが「わからない」と報告するのは失敗ではない。設計判断が必要な場面で人間に委ねる動作は正しい。「Codexが迷ったまま実装し続ける」状態の方がずっと問題だ。

---

## ハーネスで安全を担保する

エージェントを自律的に動かす設計には、安全機構が欠かせない。最低限、次の設定は入れておく。

`PreToolUse` フックで危険なコマンドをブロックする。

```bash
#!/bin/bash
# pre_tool_use.sh
TOOL_INPUT="$2"
if echo "$TOOL_INPUT" | grep -qE 'git\s+push\s+.*--force'; then
  echo "BLOCKED: git push --force は禁止" >&2
  exit 2
fi
if echo "$TOOL_INPUT" | grep -qE 'DROP\s+(TABLE|DATABASE)'; then
  echo "BLOCKED: DROP は禁止" >&2
  exit 2
fi
exit 0
```

Claude Code の権限設定でread-only操作を自動許可し、副作用のある操作は確認を求める。

```json
{
  "permissions": {
    "allow": ["Read(*)", "Bash(git status)", "Bash(git diff*)"],
    "deny":  ["Bash(git push --force*)"]
  }
}
```

ハーネス設計の全体像は[ハーネスエンジニアリングとは何か]({% post_url 2026-06-08-harness-engineering-guide %})に整理している。

---

## 段階的に始める

いきなり全体を組もうとすると、設計コストが高くなる。実際には段階的に組み上げるのがいい。

**Step 1: 2エージェント + ファイル通信**

Claude Code を orchestrator、Codex を implementer とし、`tasks.md` でタスクを共有する。agmsgなし、worktreeなしで始める。自分が手動でCodexを起動する。

**Step 2: worktreeで分離する**

Codexの作業場をworktreeに分離する。これだけでmainブランチへの誤書き込みが防げる。

**Step 3: 軽量watcherで通知を受け取る**

agmsgを導入し、DONE/BLOCKEDを検知する軽量watcherを走らせる。Codexの起動は手動のままでいい。

**Step 4: 承認付き起動**

watcherが通知してきたら確認ダイアログで承認するだけでCodexが起動する構成にする。

Step 2か3まで動けば、1人開発の生産性として十分なケースが多い。Step 4以降は、実際に詰まりが出てから考えればいい。

---

## まとめ

| 要素 | 最小構成 | 発展構成 |
| :--- | :--- | :--- |
| **役割** | orchestrator + implementer | + reviewer（ワンショット） |
| **通信** | tasks.md（ファイル） | agmsg（SQLite） |
| **並行作業** | 逐次実行 | worktreeで並行 |
| **Codex起動** | 手動 | watcher + 承認付き |
| **人間の役割** | PM + 手動起動 | PM + 承認のみ |

1人開発でマルチエージェントを組む核心は「自分が判断する範囲を絞り込むこと」だ。コードを書く時間をエージェントに渡し、自分は設計判断・承認・統合に集中する。

この分担が機能しはじめると、開発の体感速度が変わる。

---

## 参考

- [Claude と Codex のマルチエージェント引き継ぎ問題と解消パターン]({% post_url 2026-06-07-multi-agent-asymmetric-handoff %}) ── agmsg + 非対称引き継ぎの設計
- [エージェントを長く自律動作させるためのコンテキスト設計]({% post_url 2026-06-07-agent-context-management-2026 %}) ── context rot とオーケストレーター設計
- [ハーネスエンジニアリングとは何か]({% post_url 2026-06-08-harness-engineering-guide %}) ── Hooks・権限・ループ設計の全体像
- [agmsg — Cross-agent messaging for CLI AI agents](https://agmsg.cc/) ── agmsg 公式サイト
- [Claude Code Subagents](https://docs.anthropic.com/en/docs/claude-code/sub-agents) ── Claude Code の公式サブエージェント機能
