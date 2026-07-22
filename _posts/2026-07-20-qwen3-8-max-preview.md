---
layout: post
title: "Alibaba Qwen3.8-Max Preview 速報 2.4兆パラメータのマルチモーダルモデル"
subtitle: Kimi K3対抗で発表されたQwenシリーズ最新プレビュー
date: 2026-07-20 11:00:00 +0900
categories: AI開発
tags: ["Qwen", "AI", "LLM", "OSS"]
lang: ja
image:
  path: /assets/images/posts/2026-07-20-qwen3-8-max-preview/eyecatch.png
  alt: 幕がまだ半分かかった巨大な飛行船を披露する紙コラージュ調のイラスト。傍らにはすでに披露済みの小型飛行船が浮かんでいる
---

[前の記事]({% post_url 2026-07-20-kimi-k3-setup %})でMoonshot AIのKimi K3を扱ったが、その2日後にAlibabaがQwenシリーズの新モデルを発表した。まだプレビュー段階で確定情報は少ないが、現時点で分かっている範囲を速報としてまとめる。内容は2026年7月20日時点の情報に基づき、今後の発表で変わる可能性がある。

## 何が発表されたか

Alibabaは2026年7月19日、上海で開催されたWAIC（World AI Conference）でQwen3.8-Max-Previewを発表した。パラメータ数は2.4兆で、Qwenチームとして初めて1兆パラメータを超えるマルチモーダルモデルになる。画像・動画・文書の処理に対応する。

発表のタイミングは、Moonshot AIが7月16日に2.8兆パラメータのオープンウェイトモデルKimi K3を発表した直後にあたる。中国AI企業間の競争が発表サイクルにも表れている形だ。

## 位置づけの主張

Alibabaは、Qwen3.8が前世代のQwen3.7-Maxを上回り、特にフルスタック開発・データ分析・オフィス業務などのコーディング／生産性タスクで強いとしている。また性能面では「Claude Fable 5に次ぐ」という位置づけを自称しているが、この時点で第三者ベンチマークは公開されていない。

## 提供状況

現在利用できるのはPreview版のみで、Alibaba Token Plan・Qoder・QoderWork経由、通常価格の10%で提供されている。OpenAI・Anthropic互換のプロトコルに対応しており、既存のコーディングエージェントをハーネス側の改修なしに接続できる点は実務上の利点になりそうだ。

オープンウェイト版は「近日公開」とアナウンスされているが、日付・ライセンス・Hugging Faceリポジトリはまだ発表されていない。もし実現すれば、Kimi K3（2.8兆パラメータ）を超える過去最大級のオープンウェイトモデルになる。

## 現時点でのまとめ

| 項目 | 内容 |
| :--- | :--- |
| 発表日 | 2026年7月19日（WAIC上海） |
| パラメータ数 | 2.4兆（Qwen初のマルチモーダル1兆超） |
| 現在の提供形態 | Preview版のみ（Token Plan / Qoder / QoderWork） |
| オープンウェイト | 「近日公開」、日付未定 |
| ベンチマーク | 未公開 |

ベンチマークとオープンウェイト公開の詳細が出た段階で、Kimi K3との比較も含めて改めて記事にする。

## 参考

- [Alibaba Previews Qwen3.8-Max, a 2.4 Trillion-Parameter Multimodal Model](https://www.marktechpost.com/2026/07/19/alibaba-previews-qwen3-8-max-a-2-4-trillion-parameter-multimodal-model-days-after-moonshots-kimi-k3-open-weight-launch/)
- [Alibaba's Qwen takes on Kimi K3 with open-weight Qwen 3.8](https://the-decoder.com/alibabas-qwen-takes-on-kimi-k3-with-open-weight-qwen-3-8-says-model-is-second-only-to-fable-5/)
- [Alibaba Launches Qwen 3.8 With 2.4 Trillion Parameters, Claims Near-Frontier Performance](https://mlq.ai/news/alibaba-launches-qwen-38-with-24-trillion-parameters-claims-near-frontier-performance/)
