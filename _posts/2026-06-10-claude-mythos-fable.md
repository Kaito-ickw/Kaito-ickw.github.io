---
layout: post
title: "Claude Mythos（Fable）とは何か"
subtitle: Anthropic が2026年6月9日に公開した新最上位モデルの仕組みと位置づけ
categories: AI開発
tags: ["Claude", "LLM", "AIセーフティ"]
lang: ja
---

2026年6月9日、Anthropic は Claude Fable 5 を一般公開した。同時に、安全対策を一部解除した Claude Mythos 5 も招待制で提供を開始している。「Mythos」というモデルの名前を初めて聞いた人も多いだろう。この記事では、Mythos と Fable の関係、性能、安全機構、利用条件を整理する。

---

## 名前の由来

「Fable」はラテン語 _fabula_（語られたもの）に由来し、ギリシャ語 _mythos_（神話・物語）と意味的に対応する言葉だ。ひとつの基盤モデルに対して、制約の強い一般公開版を Fable、制約を外した研究・企業向け版を Mythos と名づけている。

---

## Mythos の登場背景

Mythos は 2026年4月に初めて公表された。当時 Anthropic は、このモデルを一般公開しない方針を明言していた。理由は性能の高さそのものにある。ソフトウェアの脆弱性検出・悪用、化学・生物学的な危険物製造支援、モデルのウェイト蒸留といった領域で、従来モデルを大きく超えた能力を持つと評価されたからだ。

代わりに Anthropic は「Project Glasswing」と呼ぶ招待制のプログラムを立ち上げ、約50社のサイバーセキュリティ・生物研究パートナーに限定提供した。このプログラムを通じて、重要インフラのソフトウェアにある1万件以上の脆弱性が特定されたと報告されている。

---

## 一般向けに出てきた Fable とは

Fable 5 は Mythos 5 と同じ基盤モデルだ。違いは「安全分類器（safety classifier）」の有無だけになる。

Fable 5 には独立した AI 分類器が組み込まれており、以下の3領域に関するリクエストを検出する。

- サイバーセキュリティ（攻撃・脆弱性悪用・防御回避など）
- 生物学・化学（危険物製造に関わる内容）
- モデル蒸留（ウェイトの抽出・複製に関わる内容）

これらに該当すると判断された場合、Fable 5 は回答を拒否するのではなく、Claude Opus 4.8 が代わりに応答する。ユーザーにはフォールバックが発生したことが通知される。

このフォールバックが実際に発生するのは全セッションの5%未満で、残りの95%超では Mythos 5 と実質的に同じ性能で動作する。

---

## 性能

ベンチマーク上の位置づけは明確で、Opus 4.8 を超える新しい最上位ティアとして設計されている。

主な結果:

- Hex の主要分析ベンチマークで、LLM として初めて **90%** を達成
- Cognition FrontierCode では Diamond レベル **13.4%** で1位
- 創薬プロセスの一部で最大 **10倍** の速度向上を示したケースがある
- 研究者が生成した科学的仮説のうち **80%** を人間の研究者が支持する結果が得られたと報告されている

これらは Anthropic の発表ベースの数値であり、独立した再現検証はまだ十分ではない。数字は参考程度に扱うのが妥当だ。

---

## Mythos 5 の現在の提供範囲

Mythos 5 は現時点で一般には提供されていない。アクセスできるのは以下に限られる。

- Project Glasswing の既存パートナー（サイバーセキュリティ分野の制約が解除された版）
- Anthropic が指定した生物学研究者（生物・化学分野の制約が解除された版）

Anthropic は今後、信頼済みアクセスプログラムを通じて対象を拡大する方針を示しているが、具体的なスケジュールは未定だ。

---

## 価格と提供方法

| プラン | 提供開始 | 備考 |
| :--- | :--- | :--- |
| Claude API / 消費量課金 Enterprise | 2026年6月9日〜 | 即時フル利用可 |
| Pro / Max / Team / 席数課金 Enterprise | 2026年6月9日〜 | 6月22日まで追加料金なし、以降はクレジット消費 |

API 価格は入力 **$10/百万トークン**、出力 **$50/百万トークン**。Opus 4.8 の2倍に当たる。一方で、2026年4月に限定公開されていた Mythos Preview（$25/$125）の半額以下まで下がっている。

---

## 開発者として押さえておく点

Fable 5 を API で使う場合、フォールバック発生時の課金と挙動を理解しておく必要がある。Fable 5 のレートで呼んでいたつもりが、Opus 4.8 が応答するケースがある。Anthropic は Classifier Cookbook にフォールバックと請求の詳細をまとめている。

プロンプトで意図的に安全分類器を回避しようとする行為は利用規約違反になる。分類の境界は現状かなり広めに設定されており（正規のバイオメディカル研究も一部引っかかると Anthropic 自身が認めている）、今後の調整が予告されている。

---

## まとめ

Mythos/Fable の構成をひとことでいうと、「強力なモデルをそのまま出すのではなく、危険な問い合わせは別モデルに流す形で一般公開した」ということだ。

モデル性能という軸では確実に上位ティアが開いた。AIセーフティという軸では、制約の強さと用途のトレードオフを構造で解こうとしているのが今回の設計の特徴だ。Fable がどこまで実際の用途で Opus 4.8 の上位互換として使えるかは、今後の実用報告が蓄積されるにつれてより明確になるだろう。

---

## 参考

- [Claude Fable 5 and Claude Mythos 5 – Anthropic](https://www.anthropic.com/news/claude-fable-5-mythos-5)
- [Anthropic releases Claude Fable 5 – TechCrunch](https://techcrunch.com/2026/06/09/anthropic-released-claude-fable-5-its-most-powerful-model-publicly-days-after-warning-ai-is-getting-too-dangerous/)
- [Claude Fable 5 & Mythos 5: The Frontier, Split in Two – Digital Applied](https://www.digitalapplied.com/blog/claude-fable-5-mythos-5-release-benchmarks-2026)
- [Classifier fallback and billing for Claude Fable 5 – Claude Cookbook](https://platform.claude.com/cookbook/fable-5-fallback-billing-guide)
