---
layout: post
title: "エージェントの自律性とコンテキスト管理 ── 2026年6月時点の実態と対処法"
subtitle: context rot・compaction・外部メモリ・チェックポイント、4つのアプローチを整理する
categories: 開発
tags: ["マルチエージェント", "コンテキスト管理", "Claude Code", "Codex CLI", "LLM", "AI開発"]
lang: ja
ref: agent-context-management-2026
---

エージェントに多くのタスクを任せるほど、コンテキスト管理は難しくなる。

短い1回きりの指示では問題が出にくい。しかし `/monitor` で待機し続けるClaudeや、複数タスクを連続処理するCodexは、会話履歴が積み上がり、やがてモデルの挙動が変わってくる。「clearをどこでやるか」「compactで何が消えるか」が気になるのはそのためだ。

この記事では、この問題が2026年6月時点でどのように理解され、どんな手段で対処されているかを整理する。

---

## まずコンテキスト管理が難しい理由を整理する

「コンテキストが上限に達したら困る」という理解は正しいが、それだけでは不十分だ。実際の問題はもう少し早く始まる。

### context rot（コンテキスト腐敗）

2025〜2026年にかけて「context rot」という概念が定着した。コンテキスト窓を使い切る前から、LLMの出力品質が低下し始める現象だ。

ChromaDBが18のフロンティアモデルを対象に実施した研究では、**全モデルで入力が長くなるほど出力品質が下がる**ことが確認されている。

主な原因は3つある。

**lost-in-the-middle効果:** トランスフォーマーは文脈の先頭と末尾には注意を払いやすいが、中間部分への注意が薄れる。精度が30%以上落ちるケースも報告されている。

**attention計算量の問題:** 10万トークンの文脈は100億のペアワイズ関係を意味する。処理コストが二乗的に増加するため、長いコンテキストは全体的に精度が下がりやすい。

**意味的に近い無関係コンテンツによる汚染:** 試行錯誤の過程で蓄積した「うまくいかなかったアプローチ」が、意味的に関連しているがゆえにモデルを誤誘導する。

コーディングエージェントにとって、context rotは「頭が良いのに正しく動かない」という形で現れる。問題を解く能力はあっても、積み上がったノイズが邪魔をする。

---

## 対処法の全体像

2026年時点での対処は、大きく4つの層で行われている。

```
Layer 1: ツール内蔵のcompaction
         │ Claude Code / Codex CLI / OpenCode が独自実装
         │ セッション内でコンテキストを要約・圧縮

Layer 2: 外部メモリ（セッション間・エージェント間の記憶）
         │ Letta / Mem0 / Hindsight などのフレームワーク
         │ セッションをまたいで情報を持ち越す

Layer 3: チェックポイント・再開（プロセスとしての耐障害性）
         │ Google ADK / Microsoft Agent Framework
         │ 実行状態を保存してクラッシュ後も再開

Layer 4: タスク設計（そもそもコンテキストを積ませない）
         │ 1タスク1セッション・外部状態を正本にする
         │ ツールではなく設計で解決する
```

それぞれを具体的に見ていく。

---

## Layer 1: ツール内蔵のcompaction

### Claude Code

Claude Codeは、コンテキストが上限に近づくと自動でcompactionを実行する。

**自動発火のタイミング:**

- 200Kトークンモデル: ~167K（~83%）付近でトリガー
- Opus 4.7 [1M]モデル: ~367Kトークン前後でトリガー（GitHub issueで報告されている実測値。上限に対してかなり早い段階で発火する）

環境変数 `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` で閾値を上書きできる（1〜100の整数）。

**compactionの内部処理:**

Claude Codeのcompactionは単純な要約ではなく、9つのセクションに分けた構造化サマリーを生成する。セッションの目的・完了済みタスク・保留中の問題・コードの変更・ツール呼び出し結果などが分類して保存される。

さらに、Claude Codeはプロンプトキャッシュとの親和性が高い設計になっている。他のツールはcompaction後のメッセージ構造がキャッシュと衝突しやすいが、Claude Codeは静的部分をキャッシュヒットしやすいよう構成している点が特徴的だ（他ツールとの詳細比較はGitHub GistのContext Compaction Researchに詳しい）。

**手動compaction:**

```bash
/compact
# または カスタム指示付きで
/compact レビュー済みの変更はすべて要約に含めること
```

**API経由のcompaction:**

```python
# Messages API でcompactionを有効化
response = client.messages.create(
    model="claude-opus-4-8-20251001",
    max_tokens=8096,
    context_management={
        "strategy": {
            "type": "compact_20260112",
            "trigger": {
                "type": "input_tokens",
                "value": 100000  # カスタム閾値
            }
        }
    },
    messages=[...]
)
```

ベータヘッダー `compact-2026-01-12` を付与することでも有効化できる。

---

### Codex CLI

Codex CLIは、v0.128からネイティブのMemoriesシステムを導入した。ただし**デフォルトは無効**だ。

**コンテキスト圧縮の仕組み:**

Codexは圧縮先のモデルによって2つのパスを使い分ける。

- Codexモデルの場合: OpenAIのremote `compact()` エンドポイントを呼び出し、AES暗号化されたblobとして返す
- 非Codexモデルの場合: ローカルのLLMで要約を生成する

一般的な実装セッション（ファイル読み込み・テスト実行・差分の反復）では**20〜30分以内に150,000〜200,000トークン**を消費しうる。非自明なリファクタリングは1セッションで200Kトークン窓を使い切ることもある。

**Memoriesシステム（v0.128〜）:**

```toml
# ~/.codex/config.toml
[memories]
enabled = true
idle_hours_before_extraction = 2  # セッションがアイドルになってからの待機時間
max_thread_age_days = 30          # 対象にするセッションの最大期間
```

Memoriesは、セッション終了後にバックグラウンドで動く2段階パイプラインで動作する。

1. **Stage 1:** セッション全体からエージェントが使えるインサイトを抽出
2. **Stage 2:** 複数セッションをまたいだ統合（consolidation）

抽出されたメモリは次のセッション開始時に自動注入される。使われなかったメモリは `max_unused_days` 経過後に削除される。

Codex CLIはすべてのセッションを `~/.codex/sessions/` にJSONLで保存している。`codex resume --last` で直前のセッションに戻ることも可能だ。

---

### OpenCode

OpenCodeはcompactionをエージェント自身に判断させるアプローチを取る。

モデルには `Compress` ツールが提供されており、タスク完了の区切りなど、モデルが適切と判断したタイミングで自らcompactionを呼べる。閾値は96〜99%と遅い設定で、それまでの間は20,000トークン以上かつ最後の40,000トークンを保護した状態でpruningを先行させる。

「いつcompactするかをモデルが決める」というこのアプローチは、タスク境界でのcompactionを自然に促しやすい反面、モデルの判断が外れると遅すぎる圧縮が起きる。

---

## Layer 2: 外部メモリ

セッション内のcompactionは同一セッションの長さを制御するが、セッションをまたいだ記憶は別の問題だ。複数タスクにわたって「以前の設計判断」「済みの作業」「ユーザーの好み」を引き継ぐには外部メモリが必要になる。

### Letta（旧MemGPT）

LettaはOSのメモリ階層を模倣した3層アーキテクチャを実装する。

```
core memory    ── 常に文脈に入る（RAMに相当）
                  エージェントの基本的な目標・現在の作業状態

archival memory── 外部の検索可能なベクトルストア（ディスクに相当）
                  過去の実装履歴・設計判断・調査結果

recall memory  ── 会話履歴のサマリー
```

重要なのは、エージェント自身がメモリ操作関数（`core_memory_append`、`archival_memory_search`など）をツールとして呼べる点だ。モデルは「何を覚えておくか」「何を検索するか」を能動的に判断する。

グラフ拡張を加えたメモリ検索では、平均的なRAGと比較してコンテキスト依存クエリで約90%の精度（RAGは約60%）を達成した研究もある（Mem0/ICLR 2026報告）。

### Mem0

Mem0は特定フレームワークに依存しない、クロスエージェントの永続メモリ層として機能する。

2026年4月に発表された新アルゴリズムの特徴：

- **シングルパス階層抽出:** 1回のパスでユーザーの事実・エージェントの推薦・手続き的パターンを抽出
- **マルチシグナル検索:** 意味的類似度・時系列・多段推論を組み合わせた検索
- 時系列クエリで旧アルゴリズム比 **+29.6ポイント**
- 多段推論で **+23.1ポイント**

Mem0はAnthropicのSDK・OpenAI Agents SDK・Google ADKの全ての主要フレームワークと統合しており、複数エージェントが同じメモリ層を参照できる。

### サードパーティMCPメモリサーバー

Codex CLIのMemoriesの代替として、MCP（Model Context Protocol）経由のメモリサーバーが増えている。

| サービス | 特徴 |
| :--- | :--- |
| Hindsight | セッションごとのインサイト抽出・ベクトル検索 |
| Basic Memory | MarkdownファイルベースのシンプルなMCPサーバー |
| ctx-memory | コンテキスト軽量化に特化 |
| Mem0 MCP | Mem0のメモリ層をMCP経由で利用 |

これらはClaude CodeとCodex CLIのどちらからも利用でき、エージェント間でメモリを共有することも可能だ。

---

## Layer 3: チェックポイントと再開

「コンテキストを圧縮する」のではなく「状態を外部に保存して、プロセスがクラッシュしても再開できる」アプローチだ。数分で終わるタスクより、数時間〜数日にわたるワークフローで有効になる。

### Google ADK

Google ADK（Agent Development Kit）はCheckpointとResume機能を提供する。

- ツール呼び出しのたびに自動でチェックポイントを作成
- コンテナがクラッシュしても、現在のステップを読み取って再開
- `DatabaseSessionService`（SQLite/Cloud SQL）で会話状態を永続化
- 人間の承認待ちなど「何日も止まる」フローにも対応（Human-in-the-Loop）

セッションの状態は `state_delta` として記録されるため、エージェントが何をした後に止まったかが外部から確認できる。

### Microsoft Agent Framework（BUILD 2026）

BUILD 2026で発表されたMicrosoftのAgent Harnessは、長時間セッションをまたぐコンテキスト管理をフレームワーク側で担う。ループ中のコンテキスト上限到達を検知し、自動でchat historyをcompactして続行する仕組みを提供する。

---

## Layer 4: タスク設計で解決する

ツールに頼る前に設計で回避できる部分もある。2026年の実装者の経験から共有されているプラクティスをまとめる。

### 1タスク1セッション

Codexのターンを1タスクで完結させる。長いターンで複数タスクをまたぐのではなく、タスクが完了したらセッションを終了し、次のタスクで新しいセッションを開始する。

```text
# 避けたいパターン
1つのCodexターンで: task-001実装 → task-002実装 → task-003実装

# 推奨パターン
Codex session 1: task-001のみ → DONE → セッション終了
Codex session 2: task-002のみ → DONE → セッション終了
```

コンテキストが汚染されていない状態で各タスクを始められる。また、task単位でセッションログが残るため、どのタスクでどの判断をしたか後から追える。

### 外部状態を正本にする

コンテキストに「現在の状態」を持たせると、compactやclearのたびに状態が失われる。agmsgの履歴・gitのコミット・AGENTS.mdを正本にし、コンテキストはそこから読める参照として扱う。

```text
# コンテキスト依存（fragile）
「前回の会話で〇〇と決めた」

# 外部状態依存（robust）
「AGENTS.mdに記録した設計判断を読んで実装する」
「agmsgのDONEメッセージを確認してから次に進む」
```

### TAおSKメッセージに文脈を詰める

compact後やclear後でも動けるよう、TASKとCHANGESのメッセージ自体に必要な文脈を含める。

```text
# 文脈依存（fragile）
CHANGES task-002 -> backend 前回の指摘を直して

# 自己完結（robust）
CHANGES task-002 -> backend
  worktree: /workspace/.worktrees/ledger
  branch: feat/ledger-api
  指摘: src/api/entries.py:45
        外部キー account_id の存在確認が抜けている
        Account.get(id) でNoneを返す場合に400を返すこと
```

### compactはタスク境界で行う

最も失うものが少ないタイミングは、タスクが完了した直後だ。

```text
DONE task-001 を受け取った
  → git merge / push 完了
  → ここで /compact
  → 次のTASKを送信
```

完了したタスクの詳細はgitに保存されており、compactでその詳細が消えても問題ない。

---

## 各ツールのcompaction比較

| | Claude Code | Codex CLI | OpenCode |
| :--- | :--- | :--- | :--- |
| **自動発火閾値** | ~83-95%（モデルにより異なる） | 独自しきい値 | 96-99%（遅め） |
| **圧縮方式** | 構造化9セクションサマリー | remote compact() or ローカルLLM | pruning → LLMサマリー |
| **誰が判断するか** | ツール自動 | ツール自動 | モデルが自律判断 |
| **プロンプトキャッシュ** | 親和性高 | compaction後にキャッシュ破棄あり | 要確認 |
| **セッション永続化** | なし（会話内のみ） | ~/.codex/sessions/ にJSONL | なし |
| **クロスセッションメモリ** | なし（標準） | Memoriesシステム（要有効化） | なし（標準） |
| **手動compact** | /compact | /compact | Compressツール（モデル呼び出し） |

---

## マルチエージェント構成での実際的な対処

agmsg + Claude Code（monitor）+ Codex（turn）の構成に当てはめると、どう考えるか。

**Claudeのコンテキスト管理:**

Claudeはmonitorモードで複数タスクを処理し続ける。タスクが完了するたびに `/compact` を実行することで、必要な文脈（現在進行中のタスク状態・設計の方針）を要約として残しつつ、不要な詳細を切り落とせる。

タスク完了の節目に `agmsg send` 実行直後に `/compact` する習慣をつけることが現状の最善だ。StatusLineフックでコンテキスト残量を監視して警告を出す仕組みも有効。

**Codexのコンテキスト管理:**

Codexは1タスク1ターンにするのが最もシンプルだ。タスクが完了したらDONEを送ってターンを終了し、次のTASKを受けたときに新ターンで開始する。

これだと「CHANGES後にCodexが自分で気づいて再開できない」問題（前の記事で扱った非対称な引き継ぎ問題）は残るが、コンテキスト管理は単純になる。

Codex CLIのMemoriesシステムを有効化しておくと、「このプロジェクトのコーディング規約」「よく使うパターン」などがセッション間で引き継がれる。ただし実装の具体的な経緯はgitとagmsgに残すのが正本だ。

**外部メモリの導入タイミング:**

Mem0やLettaのような外部メモリは、以下の条件が揃ってから検討するのが現実的だ。

- 同一エージェントに数週間以上のタスクを連続して与える
- 複数エージェントが同じ「プロジェクト知識」を共有する必要がある
- セッション間での設計判断の引き継ぎが繰り返し問題になっている

個人・小規模開発の初期フェーズでは、AGENTS.mdとagmsgのメッセージ履歴を活用する方が導入コストが低い。

---

## まとめ

2026年6月時点でのコンテキスト管理の実態は次のようになっている。

1. **コンテキストウィンドウが大きくなってもcontext rotは起きる**。問題は上限だけでなく、長い文脈での注意力低下だ

2. **CLIツールは独自のcompactionを実装している**。Claude Codeの構造化サマリー、Codex CLIのMemories、OpenCodeのモデル自律判断、それぞれアプローチが異なる

3. **外部メモリ（Letta、Mem0）はセッション間の記憶を担う**。フレームワーク選定より「何を記憶させるか」の設計が重要

4. **Google ADKなどはプロセスの耐障害性で解決する**。チェックポイント・再開の仕組みで長時間ワークフローに対応

5. **設計で回避できる部分が大きい**。1タスク1セッション・外部状態を正本にする・メッセージに文脈を詰める

「いつcompactするか」という問いへの答えは、**タスク完了の直後**だ。それ以外の場面では、まずタスクを区切りよく終わらせることを優先する方が、コンテキストの質を保ちやすい。

---

## 参考情報

### コンテキスト管理の実態

- [Context Compaction Research: Claude Code, Codex CLI, OpenCode, Amp](https://gist.github.com/badlogic/cd2ef65b0697c4dbe2d13fbecb0a0a5f) — GitHub Gist。主要ツールのcompaction実装を横断比較した研究
- [Context Compaction Deep Dive: Codex CLI, Claude Code, and OpenCode](https://codex.danielvaughan.com/2026/04/14/context-compaction-deep-dive-codex-cli-claude-code-opencode/) — 各ツールのcompaction戦略の詳細比較
- [Context Window Management and Session Lifecycle for Long-Running AI Agents](https://zylos.ai/research/2026-03-31-context-window-management-session-lifecycle-long-running-agents/) — Zylos Research。長期運用エージェントのコンテキスト設計

### context rot

- [Context Rot: Why LLMs Degrade as Context Grows](https://www.morphllm.com/context-rot) — context rotの定義・メカニズムの解説
- [Context Rot in LLMs: Why AI Systems Degrade Over Time](https://medium.com/@arsalkhan963/context-rot-in-llms-why-ai-systems-degrade-over-time-ba300e39aef4) — lost-in-the-middle効果の詳細
- [How to Use the /compact Command in Claude Code to Prevent Context Rot](https://www.mindstudio.ai/blog/claude-code-compact-command-context-management) — MindStudio。実践的な使い方

### Claude Code compaction

- [Compaction — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/compaction) — Anthropic公式ドキュメント
- [Automatic context compaction — Claude Cookbook](https://platform.claude.com/cookbook/tool-use-automatic-context-compaction) — APIでのcompaction有効化方法
- [Claude Code Context Buffer: The 33K-45K Token Problem](https://claudefa.st/blog/guide/mechanics/context-buffer-management) — 実測値に基づくバッファ量の解説

### Codex CLI

- [Codex CLI Memories: Native Session Persistence](https://codex.danielvaughan.com/2026/05/01/codex-cli-memories-persistent-context-session-memory-ecosystem/) — v0.128のMemoriesシステムとサードパーティエコシステム
- [Codex CLI Memory: How It Works + What Mem0 Adds](https://mem0.ai/blog/how-memory-works-in-codex-cli) — Mem0との統合
- [Context Compaction Architecture — Codex CLI](https://codex.danielvaughan.com/2026/03/31/codex-cli-context-compaction-architecture/) — Codex CLIのcompactionアーキテクチャ詳細

### 外部メモリ・フレームワーク

- [State of AI Agent Memory 2026](https://mem0.ai/blog/state-of-ai-agent-memory-2026) — Mem0によるエージェントメモリの現状レポート
- [Memory for Autonomous LLM Agents: Mechanisms, Evaluation, and Emerging Frontiers](https://arxiv.org/html/2603.07670v1) — 学術論文。エージェントメモリの体系的整理
- [Agent Memory at Scale 2026: Letta, Zep, Mem0, and LangMem Compared](https://agentmarketcap.ai/blog/2026/04/10/agent-memory-vendor-landscape-2026-letta-zep-mem0-langmem) — 主要メモリフレームワークの比較

### チェックポイント・長時間ワークフロー

- [Build Long-running AI agents that pause, resume, and never lose context with ADK](https://developers.googleblog.com/build-long-running-ai-agents-that-pause-resume-and-never-lose-context-with-adk/) — Google Developers Blog
- [Resume Agents — Agent Development Kit (ADK)](https://google.github.io/adk-docs/runtime/resume/) — ADK公式ドキュメント
- [Microsoft Agent Framework at BUILD 2026](https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-at-build-2026-announce/) — Agent Harnessのコンテキスト管理機能
