---
layout: post
title: "Kimi K3 vs Claude Fable 5 vs GPT-5.6 Sol フロンティア比較 (2026年7月版)"
subtitle: オープンウェイト最大級モデルの実力と位置づけ
date: 2026-07-20 09:00:00 +0900
categories: AI開発
tags: ["AI", "LLM", "Kimi", "OSS"]
lang: ja
image:
  path: /assets/images/posts/2026-07-20-kimi-k3-vs-fable-gpt/eyecatch.png
  alt: 密閉された2艇のボートに、骨組みがむき出しの大きな1艇が並びかけるリソグラフ調のレースイラスト
---

Moonshot AIが2026年7月16日にKimi K3を発表した。「Fable級」という評判をSNSで見かけるが、実際のところどうなのか。どこの会社のモデルで、Claude Fable 5やGPT-5.6 Solと比べて何が強く何が弱いのかを、公開ベンチマークと第三者評価をもとに整理する。内容は2026年7月20日時点の情報に基づく。

## Kimi K3とは

Kimi K3は中国のスタートアップMoonshot AI（月之暗面）のフラグシップモデルである。Moonshot AIはDeepSeekと並ぶ中国AI企業の代表格で、KimiシリーズをWebアプリ・API・オープンウェイトの3形態で提供している。

K3の主な仕様は次のとおり。

- 総パラメータ数 2.8兆。発表時点で史上最大のオープンウェイトモデル
- コンテキストウィンドウは100万トークン
- Kimi Delta Attention（KDA）とLatentMoE構成。896エキスパートのうち16を活性化し、スケーリング効率はK2の約2.5倍とされる
- モデルウェイトは2026年7月27日までに公開予定

「オープンウェイトのままフロンティアに追いついた」という点が、発表直後から市場でDeepSeekショックの再来として扱われた理由である。

## ベンチマークで見る位置づけ

Moonshot自身の公表は「Claude Opus 4.8やGPT-5.5には勝つが、Claude Fable 5とGPT-5.6 Solには総合で及ばない」という整理で、第三者機関Artificial Analysisの評価もほぼ同じ結論になっている。

| 指標 | Kimi K3 | GPT-5.6 Sol | Claude Fable 5 |
| :--- | :--- | :--- | :--- |
| AA Intelligence Index | 57.1% | 58.9% | **59.9%** |
| FrontierSWE（コーディング） | **77.8** | 77.6 | 76.8 |
| Frontend Code Arena | **1位（1,679）** | ─ | 2位 |
| GDPval v2（実務作業） | 1,668 | ─ | **1,760** |
| GPQA Diamond | 93.5%（オープンウェイト最高） | ─ | ─ |

両ベンダーが共通で報告している14ベンチマークの勝敗は、Fable 5が8勝、K3が6勝。総合ではFable 5がリードするが、一方的な差ではない。

領域別に見ると傾向がはっきりする。

- **コーディング**: FrontierSWEとFrontend Code ArenaでK3が首位。コーディング用途に限れば「Fable級」という評判は誇張ではない
- **実務・知識労働**: GDPval v2ではFable 5と92ポイント差。両者が競う指標の中で最も開きが大きい
- **弱点**: ハルシネーション率が前世代の39%から51%へ悪化したという指摘がある。精度が上がる一方で、断定的に間違える頻度は増えた

## 価格

| モデル | 入力（$/1Mトークン） | 出力（$/1Mトークン） |
| :--- | :--- | :--- |
| Kimi K3 | 3 | 15 |
| GPT-5.6 Sol | 5 | 30 |
| Claude Fable 5 | 10 | 50 |

K3はFable 5の約1/3の価格だが、前世代K2.6（$0.95 / $4）からは大幅な値上げで、Claude Sonnet 5と同水準になった。「中国AI＝激安」という前提が崩れ始めたシグナルとして受け止められている。1タスクあたりの実測コストは約$0.94で、GPT-5.6 Solと同程度という評価もある。

## まとめ

「Fable級」は半分正しい。コーディングとエージェントタスクではFable 5と互角以上、総合知能と実務品質では一段下、価格は1/3、そしてオープンウェイトという独自の価値がある。プロプライエタリ2強に依存しない選択肢として、実運用で試す価値は十分にある。

実際にClaude CodeからK3を使うための導入手順は[Claude Code環境にKimi K3を導入する]({% post_url 2026-07-20-kimi-k3-setup %})にまとめた。

## 参考

- [Moonshot releases 2.8-trillion-parameter Kimi K3 (Tom's Hardware)](https://www.tomshardware.com/tech-industry/artificial-intelligence/moonshot-releases-2-8-trillion-parameter-kimi-k3)
- [Kimi K3, and what we can still learn from the pelican benchmark (Simon Willison)](https://simonwillison.net/2026/Jul/16/kimi-k3/)
- [Kimi's open model K3 nears GPT-5.6 Sol and Fable 5 (The Decoder)](https://the-decoder.com/kimis-open-model-k3-nears-gpt-5-6-sol-and-fable-5-while-signaling-the-end-of-super-cheap-chinese-ai/)
- [China's Moonshot AI unveils Kimi K3 (CNBC)](https://www.cnbc.com/2026/07/17/moonshot-ai-kimi-k3-model-openai-anthropic-china.html)
- [Artificial Analysis Intelligence Index Leaderboard (BenchLM)](https://benchlm.ai/benchmarks/artificialAnalysis)
