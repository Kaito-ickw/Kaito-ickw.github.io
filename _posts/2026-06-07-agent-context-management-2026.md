---
layout: post
title: "エージェントを長く自律動作させるためのコンテキスト設計"
subtitle: 下位エージェントと上位エージェントで問題が非対称である理由と、2026年時点の解決アプローチ
categories: AI開発
tags: ["マルチエージェント", "コンテキスト管理", "Claude Code", "Codex CLI", "LLM"]
lang: ja
ref: agent-context-management-2026
image:
  path: /assets/images/posts/2026-06-07-agent-context-management-2026/eyecatch.png
  alt: 完了した作業を外部アーカイブへ移して机を空けるミニチュアの管制室
---

エージェントに多くのタスクを自律的にやらせようとすると、ある非対称な問題にぶつかる。

**下位エージェント（実装担当）** はタスクが終わるたびにセッションを終了できる。次のタスクは白紙のコンテキストで始まる。コンテキスト管理の問題はあまり起きない。

**上位エージェント（オーケストレーター）** はそうはいかない。「何が済んで・何が残っていて・次は何か」を複数タスクにわたって把握しつづける必要があるため、長く生かしたい。しかし長く生かすほどコンテキストが積み上がり、やがてモデルの挙動が変わってくる。

この問題は「いつclearするか」ではなく、**オーケストレーターの設計**の問題だ。2026年6月時点で取られている解決アプローチをまとめる。

---

## なぜ長いコンテキストは問題になるのか

「上限に達したら困る」という理解は正しいが、問題はそれより前に始まる。

### context rot（コンテキスト腐敗）

コンテキスト窓が埋まる前から、LLMの出力品質が低下し始める。2025〜2026年にかけて「context rot」と呼ばれるようになった現象だ。

ChromaDBが18のフロンティアモデルを対象に実施した研究では、**全モデルで入力が長くなるほど出力品質が下がる**ことが確認されている。

主な原因は3つだ。

**lost-in-the-middle効果:** トランスフォーマーは文脈の先頭と末尾には注意を払いやすいが、中間部分への注意が薄れる。精度が30%以上落ちるケースも報告されている。

**attention計算量の問題:** 10万トークンの文脈は100億のペアワイズ関係を意味する。処理コストが二乗的に増加するため、長いコンテキストは全体的に精度が下がりやすい。

**ノイズの蓄積:** 試行錯誤の過程で積み上がった「うまくいかなかったアプローチ」が、意味的に関連しているがゆえにモデルを誤誘導する。コーディングエージェントにとってこれが一番やっかいで、「頭が良いのに正しく動かない」という形で現れる。

モデルのコンテキストウィンドウは年々拡大しているが、context rotは上限に関係なく発生する。大きくなったウィンドウは問題を先送りするが、解消はしない。

---

## 問題の非対称性

```
下位エージェント（例: Codex）
  task-001 実装 → DONE → セッション終了
  task-002 実装 → DONE → セッション終了  ← コンテキストは毎回リセット
  task-003 実装 → DONE → セッション終了

上位エージェント（例: Claude orchestrator）
  task-001 発行 → DONE受信 → レビュー → merge → task-002発行
  task-002 発行 → DONE受信 → レビュー → CHANGES → 修正待ち
  task-003 発行 → ...                             ← コンテキストが積み続ける
```

下位エージェントは1タスク1セッションにできる。タスクが完了したらセッションを終了し、次のタスクでは新しいセッションを開始する。コンテキストが汚染される前に毎回リセットされる。

上位エージェントはそれができない。なぜなら「過去のタスクの結果を踏まえて次を判断する」というのがオーケストレーターの仕事だからだ。

---

## 自律的に解決する3つのアプローチ

「人間がタイミングを判断してclearする」のは正しいが、自律性を高めるにはこれに頼れない。2026年時点で取られているアプローチは次の3つに整理できる。

### アプローチ1: サブエージェントで文脈の汚染を防ぐ

Claude Codeにはサブエージェント機能がある。子エージェントは**独立したコンテキストウィンドウで動き、結果はサマリーとして親に返ってくる**。

```
orchestrator（Claude, 長命）
  context: [タスクリスト, 設計方針, 完了済み概要, ...]

  → task-002をサブエージェントに委託
      subagent context: [task-002の仕様, ファイル読み込み結果, テスト実行ログ, ...]
      ← サマリーのみ返す: "feat/api-v2 実装完了, 3ファイル変更, テスト全通"

  orchestrator contextに追加されるのはサマリーだけ
```

子エージェントが100Kトークン消費しても、親のコンテキストには数百トークンのサマリーしか積まれない。これは「下位エージェントの文脈汚染を親から遮断する」仕組みだ。

ただし、これは「オーケストレーター自身のコンテキスト蓄積」は解決しない。タスクが増えるほど、サマリーが積み重なって親も膨らんでいく。根本的な解決にはならないが、膨らみ方を大きく抑えられる。

### アプローチ2: オーケストレーターを「薄く」設計する（Ralph Loop）

「Ralph Loop」と呼ばれるパターンが2025〜2026年に広まった。考え方はシンプルだ。

**オーケストレーターのコンテキストに状態を持たせない。状態はすべて外部に書く。**

```
while タスクが残っている:
  1. 外部ストアから現在の状態を読む（git / agmsg / ファイル）
  2. 「次にやるべきこと」を1つ判断する
  3. 下位エージェントに委託する
  4. 結果を外部ストアに書く
  5. コンテキストをclearして最初に戻る
```

各ループの終わりにclearできるのは、**判断に必要な状態がすべて外部に書かれているから**だ。コンテキストの中身は「今回の判断」だけでよく、過去のやり取りを覚えている必要がない。

```text
# 従来（コンテキスト依存）
「3つ前の会話でCHANGESを送ったあの件、どうなったか」

# Ralph Loop（外部状態依存）
ループ開始時に: agmsg inbox を確認
              → DONE task-003 を検知
              → git log で差分確認
              → 次の判断
```

agmsg + gitの構成はこの設計と相性が良い。agmsgのメッセージ履歴とgitのコミット履歴が「何が済んで何が残っているか」の外部ストアになる。

**自律的なclearの実装例（Claude Codeへの指示として）:**

```text
# CLAUDE.md または system prompt に記述
タスクが1つ完了したら（DONE受信・merge完了後）、次のタスクに移る前に
以下を実行すること:
1. 完了内容をAGENTS.mdに記録する
2. /compact を実行する
3. agmsg inbox を確認して次のタスクを取得する
```

これはモデルへの指示としてコンテキストに入れておくことで、人手なしでcompactを呼ばせられる。モデルが指示通りに動く保証は100%ではないが、「タスク完了」という明確なトリガーが存在するため、判断のぶれは起きにくい。

### アプローチ3: モデル自身がcompactを判断する（OpenCodeの方式）

OpenCodeはこの問題に対して、**モデル自身が`Compress`ツールを呼ぶ**設計を取っている。

モデルにはCompressツールが提供されており、「このタスクが終わった、今圧縮するのが適切」と判断したタイミングで自発的に呼び出せる。Claude Codeの自動compactが「上限近傍の緊急措置」として機能するのとは異なり、タスク境界という意味のある区切りで発動できる。

Claude Codeには現時点でこれに相当する機能はない。`/compact`は手動コマンドであり、自動compactは上限（〜95%）での緊急措置だ。

---

## ツール内蔵のcompactionは「緊急措置」として位置づける

ツール内蔵のcompactionは、設計で解決できなかった場合のフォールバックとして理解するのが正しい。

### Claude Code

コンテキストが上限に近づくと自動でcompactionを実行する。

- 200Kモデル: ~167K（~83%）付近でトリガー
- Opus [1M]モデル: ~367K前後でトリガー（GitHubで報告された実測値）
- `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` で閾値を調整できる

compactionは単純な要約ではなく、9つのセクションに分けた構造化サマリーを生成する（セッションの目的・完了済みタスク・保留中の問題・コードの変更など）。プロンプトキャッシュとの親和性も高く設計されており、compaction後もキャッシュヒットしやすい。

手動実行は `/compact`。カスタム指示も付けられる。

```bash
/compact 完了済みタスクの詳細は省略し、未解決の問題だけ残すこと
```

### Codex CLI

v0.128からネイティブのMemoriesシステムを導入した（デフォルト無効）。

セッション内のcompactionは、Codexモデルではremote `compact()`エンドポイント（AES暗号化blobで返る）、非Codexモデルではローカルのサマリーを使う。

```toml
# ~/.codex/config.toml
[memories]
enabled = true
idle_hours_before_extraction = 2
max_thread_age_days = 30
```

Memoriesが有効だと、セッション終了後にバックグラウンドでインサイトを抽出し、次のセッション開始時に自動注入する。「このプロジェクトのコーディング規約」「よく使うパターン」の引き継ぎに有効だ。

すべてのセッションは `~/.codex/sessions/` にJSONLで保存されており、`codex resume --last` で直前のセッションに戻れる。

### OpenCode

モデルへの`Compress`ツール提供に加え、96〜99%に達するまでは20,000トークン以上かつ最後の40,000トークンを保護したpruningを先行させる。compactionは本当の最終手段として設計されている。

---

## セッション間の記憶: 外部メモリ

同一セッション内のcompactionとは別に、**セッションをまたいだ記憶**には外部メモリが必要になる。

### Letta（旧MemGPT）

OSのメモリ階層を模倣した3層構造。

```
core memory    ── 常に文脈に入る（RAMに相当）
archival memory── 外部検索可能なベクトルストア（ディスクに相当）
recall memory  ── 会話履歴のサマリー
```

エージェント自身が`core_memory_append`・`archival_memory_search`などのツールを呼んでメモリを操作する。モデルが「何を覚えておくか」を能動的に判断する設計だ。

### Mem0

特定フレームワークに依存しないクロスエージェントの永続メモリ層。Anthropic SDK・OpenAI Agents SDK・Google ADKすべてと統合している。2026年4月のアルゴリズム更新で時系列クエリの精度が+29.6ポイント改善された。

複数エージェントが同じメモリ層を参照できるため、orchestratorとworkerでプロジェクト知識を共有できる。

### MCPメモリサーバー

Claude CodeとCodex CLIのどちらからも利用できるMCP経由のメモリサーバーが増えている。

| サービス | 特徴 |
| :--- | :--- |
| Hindsight | セッションごとのインサイト抽出・ベクトル検索 |
| Basic Memory | MarkdownファイルベースのシンプルなMCPサーバー |
| Mem0 MCP | Mem0のメモリ層をMCP経由で利用 |

**外部メモリの導入タイミング:** Mem0やLettaは、「同一エージェントに数週間以上のタスクを連続して与える」「複数エージェント間でプロジェクト知識を共有したい」場面で真価を発揮する。初期フェーズではAGENTS.md + agmsg履歴を外部ストアとして使う方が導入コストは低い。

---

## チェックポイントと再開: 別次元の耐障害性

コンテキスト管理とは別に、「プロセスがクラッシュしても再開できる」耐障害性も長時間運用では必要になる。

**Google ADK** はツール呼び出しのたびにチェックポイントを作成し、コンテナがクラッシュしても現在のステップを読み取って再開できる。`DatabaseSessionService`（SQLite/Cloud SQL）で会話状態を永続化し、数日止まる Human-in-the-Loop フローにも対応する。

**Microsoft Agent Framework（BUILD 2026）** はループ中のコンテキスト上限到達を検知し、フレームワーク側で自動compactして続行する仕組みを提供する。

---

## 整理: 何がどの問題を解くか

| 手段 | 解く問題 | 自律性 |
| :--- | :--- | :--- |
| サブエージェント（Claude Code） | 下位エージェントの文脈汚染を親から遮断 | 高（設計で解決） |
| Ralph Loop（外部状態 + clearループ） | オーケストレーター自身のコンテキスト蓄積 | 高（設計で解決） |
| CLAUDE.mdへのcompact指示 | タスク境界での自律的compact | 中（モデル依存） |
| OpenCode Compressツール | モデルが適切タイミングで自律compact | 高 |
| Claude Code 自動compact | 上限近傍の緊急措置 | 高（自動） |
| Codex CLI Memories | セッション間のインサイト引き継ぎ | 高（バックグラウンド） |
| Letta / Mem0 | クロスセッション・クロスエージェントの長期記憶 | 高（フレームワーク） |
| Google ADK checkpoint | プロセス障害からの再開 | 高（フレームワーク） |

「タスク境界でオーケストレーターを自律的にcompactする」専用機能は、2026年6月時点ではClaude Codeにはない。OpenCodeのCompressツールがそれに最も近い。Claude Codeで同等を実現するには、CLAUDE.mdへの指示またはRalph Loop設計で補う。

---

## agmsg + Claude + Codex構成への適用

この構成でオーケストレーター（Claude）のコンテキストを自律的に管理するなら、次が現実的な設計だ。

**CLAUDE.md（または system prompt）に書く:**

```text
あなたはagmsgを通じてCodexと協働するオーケストレーターです。
以下のループで動作してください:

1. agmsg inboxを確認する
2. DONEを受信したら: git mergeし、AGENTS.mdに完了を記録し、/compact を実行する
3. /compact後: agmsg inboxを再確認し、次のTASKを発行する
4. 設計上の判断が必要な場合はBLOCKEDを返し、人間に委ねる
```

**外部ストアの整備:**

```text
AGENTS.md
  ├── 完了済みタスク（task-id・branch・概要）
  ├── 現在進行中のタスク
  ├── 積み残しの設計判断
  └── 方針・制約

agmsgメッセージ履歴
  └── タスクの受け渡しと結果の正本

gitコミット履歴
  └── 実装の詳細の正本
```

Claudeがループの最初にAGENTS.mdを読めば、コンテキストをclearしても「今どこにいるか」を再構築できる。これがRalph Loopを成立させる外部状態だ。

---

## まとめ

自律エージェントのコンテキスト管理は、ツールの問題より設計の問題だ。

**下位エージェントはタスク単位でセッションを終了できる。** これは設計として明示的に選べる。

**上位エージェント（オーケストレーター）の問題は非対称だ。** 長く生かしたいが、コンテキストは積む。これを自律的に解決するには:

1. **サブエージェント**で下位の文脈汚染を親から遮断する
2. **外部ストアを正本にする**ことでclearしても再起動できる設計にする（Ralph Loop）
3. **モデルへの明示的な指示**でタスク境界でのcompactを自律的に行わせる

ツール内蔵のcompactionは上限近傍での緊急措置であり、設計の代わりにはならない。外部メモリ（Letta、Mem0）はこの上に重ねてセッション間の記憶を担う。

「いつclearするか」という問いへの答えは、**オーケストレーターがclearしても大丈夫な状態にしておく**ことだ。タイミングの問題を、設計の問題として解く。

---

## 参考情報

### コンテキスト管理とcompaction

- [Context Compaction Research: Claude Code, Codex CLI, OpenCode, Amp](https://gist.github.com/badlogic/cd2ef65b0697c4dbe2d13fbecb0a0a5f) — 主要ツールのcompaction実装を横断比較した研究
- [Context Compaction Deep Dive: Codex CLI, Claude Code, and OpenCode](https://codex.danielvaughan.com/2026/04/14/context-compaction-deep-dive-codex-cli-claude-code-opencode/) — 各ツールのcompaction戦略の詳細比較
- [Context Window Management for Long-Running AI Agents](https://zylos.ai/research/2026-03-31-context-window-management-session-lifecycle-long-running-agents/) — 長期運用エージェントのコンテキスト設計
- [Compaction — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/compaction) — Anthropic公式ドキュメント
- [Codex CLI Memories: Native Session Persistence](https://codex.danielvaughan.com/2026/05/01/codex-cli-memories-persistent-context-session-memory-ecosystem/) — v0.128のMemoriesシステム詳細

### context rot

- [Context Rot: Why LLMs Degrade as Context Grows](https://www.morphllm.com/context-rot) — context rotの定義・メカニズム
- [How to Use the /compact Command in Claude Code to Prevent Context Rot](https://www.mindstudio.ai/blog/claude-code-compact-command-context-management) — 実践的な使い方

### オーケストレーターとサブエージェント設計

- [Claude Code Subagents: A 2026 Practical Guide](https://www.tembo.io/blog/claude-code-subagents) — サブエージェントの使い方とコンテキスト分離
- [The Code Agent Orchestra](https://addyosmani.com/blog/code-agent-orchestra/) — Addy Osmani。マルチエージェントコーディングのパターン（Ralph Loopを含む）
- [Long-Running Coding Agents: The 2026 Guide](https://o-mega.ai/articles/long-running-coding-agents-the-2026-guide) — 長時間稼働エージェントの設計ガイド

### 外部メモリ・フレームワーク

- [State of AI Agent Memory 2026](https://mem0.ai/blog/state-of-ai-agent-memory-2026) — Mem0によるエージェントメモリの現状レポート
- [Memory for Autonomous LLM Agents](https://arxiv.org/html/2603.07670v1) — エージェントメモリの学術的整理
- [Agent Memory at Scale 2026: Letta, Zep, Mem0, and LangMem Compared](https://agentmarketcap.ai/blog/2026/04/10/agent-memory-vendor-landscape-2026-letta-zep-mem0-langmem) — 主要フレームワーク比較

### チェックポイント・長時間ワークフロー

- [Build Long-running AI agents that pause, resume, and never lose context with ADK](https://developers.googleblog.com/build-long-running-ai-agents-that-pause-resume-and-never-lose-context-with-adk/) — Google Developers Blog
- [Microsoft Agent Framework at BUILD 2026](https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-at-build-2026-announce/) — Agent Harnessのコンテキスト管理機能
