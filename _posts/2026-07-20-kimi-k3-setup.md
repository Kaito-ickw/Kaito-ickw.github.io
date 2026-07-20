---
layout: post
title: "Claude Code環境にKimi K3を導入する"
subtitle: Anthropic互換APIとKimi CLIの選択肢
date: 2026-07-20 10:00:00 +0900
categories: AI開発
tags: ["Kimi", "Claude Code", "CLI", "AI"]
lang: ja
image:
  path: /assets/images/posts/2026-07-20-kimi-k3-setup/eyecatch.png
  alt: 灯ったデスクランプのプラグを隣の新しいソケットへ差し替える手元を描いたリソグラフ調のイラスト
---

[前の記事]({% post_url 2026-07-20-kimi-k3-vs-fable-gpt %})でKimi K3の位置づけを整理した。ベンチマーク上はコーディングでFable 5と互角以上とされるが、自分の手元のタスクでどうかは実際に動かさないと分からない。この記事では、すでにClaude CodeとCodexの利用環境がある前提で、Kimi K3を追加導入する方法を整理する。内容は2026年7月20日時点の公式ドキュメントに基づく。

## 結論を先に

導入経路は主に4つある。既存のClaude Code環境を流用するのが最も手軽だ。

| 経路 | 向いている用途 |
| :--- | :--- |
| Claude Code + Anthropic互換API | 既存ワークフローのままモデルだけ差し替えて比較する |
| Kimi CLI（Kimi Code） | Moonshot公式のコーディングエージェントを試す |
| API直接利用（OpenAI / Anthropic互換） | 自作スクリプトやベンチマークでの検証 |
| セルフホスト（オープンウェイト） | 現実的には非推奨（後述） |

いずれもKimiのメンバーシップ（Code特典付き）またはAPIプラットフォームのクレジットが必要になる。

## Claude CodeからK3を使う

KimiのCoding APIはAnthropicプロトコル互換で、Claude Codeは環境変数の差し替えだけでK3に向けられる。

```bash
export ANTHROPIC_BASE_URL=https://api.kimi.com/coding/
export ANTHROPIC_API_KEY=<Kimi Code ConsoleのAPIキー>
export ANTHROPIC_MODEL="k3[1m]"
export CLAUDE_CODE_EFFORT_LEVEL=high
```

- APIキーは[Kimi Code Console](https://www.kimi.com/code/console)で発行する
- `k3[1m]` という表記で100万トークンコンテキストが有効になる
- 起動後に `/status` を実行し、Base URLが `https://api.kimi.com/coding/` になっていることを確認する
- thinkingを無効にするとK2.6へルーティングされる仕様のため、K3の性能を見るならthinkingは有効のままにする。`/effort` で `low` / `high` / `max` を切り替えられる

Moonshotの汎用APIプラットフォーム経由でも同様に使える。その場合は `ANTHROPIC_BASE_URL=https://api.moonshot.ai/anthropic`、モデル名は `kimi-k3[1m]` を指定する。

環境変数をシェルプロファイルへ直接書くと通常のClaude利用と衝突するため、比較検証ではエイリアスやdirenvで切り替えられるようにしておくとよい。

```bash
alias kimi-code='ANTHROPIC_BASE_URL=https://api.kimi.com/coding/ ANTHROPIC_API_KEY=$KIMI_API_KEY ANTHROPIC_MODEL="k3[1m]" claude'
```

## Kimi CLIを使う

Moonshotは公式のコーディングエージェントとしてKimi Code（CLI）も提供している。Claude Code・Codex CLIと同系統のターミナル型エージェントで、K3をネイティブに使う場合の本命はこちらになる。挙動やハーネス設計の違いも含めて比較したい場合は、Claude Code経由ではなくこちらで試す方がフェアな比較になる。

インストールと設定は[公式ドキュメント](https://www.kimi.com/code/docs/en/)に従う。プロバイダ設定でMoonshot APIキーを登録すれば動作する。

## セルフホストは現実的か

K3のウェイトは2026年7月27日までに公開予定だが、総パラメータ2.8兆のモデルであり、個人のローカルGPU環境での推論は現実的ではない。ローカル検証といっても実態はAPI経由になる。自前サービングを検討するのは、複数ノードのGPUクラスタを確保できる組織に限られる。

## 検証の観点

Claude・Codexとの実測比較をする場合、次の観点をそろえると差が見えやすい。

- 同一リポジトリ・同一Issueに対するタスク完遂率と手数
- thinkingあり（K3）とClaude Fable 5のeffort設定を同格にそろえる
- 1タスクあたりの実測コスト（K3は公称でFable 5の約1/3）
- ハルシネーション傾向。K3は前世代より断定的な誤りが増えたという指摘があるため、出力の検証コストも含めて評価する

## 参考

- [Use Kimi in Claude Code (Kimi API Platform)](https://platform.kimi.ai/docs/guide/claude-code-kimi)
- [Using in Third-Party Coding Agents (Kimi Code Docs)](https://www.kimi.com/code/docs/en/third-party-tools/other-coding-agents.html)
- [Kimi Code Overview (Kimi Code Docs)](https://www.kimi.com/code/docs/en/)
- [Kimi API Platform](https://platform.kimi.ai/)
