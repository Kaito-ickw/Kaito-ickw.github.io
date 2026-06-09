---
layout: post
title: "Android から Claude Code を使うパターンと選び方"
subtitle: "Remote Control・SSH・Termux それぞれの特徴と使い分け"
categories: AI開発
tags: ["Claude Code", "コーディングエージェント", "開発環境", "AI開発"]
lang: ja
---

メインのスマホが Galaxy Z Fold 7 になってから、移動中や自宅のソファでコードのレビューや軽い修正をスマホだけでこなせるかどうかを試してきた。

AI コーディングが広まるにつれて、「エージェントに作業を投げておき、スマホで進捗確認・指示出し・レビューをする」という使い方が現実的になってきている。Claude Code を Android から使うパターンはいくつかあり、それぞれに前提と制約が異なる。実際の利用事例をもとに整理する。

## パターンの全体像

| パターン | 前提 | セットアップ | 安定性 |
|:---|:---|:---:|:---:|
| A. Remote Control（公式） | PC / VPS が常時起動 | 低 | 高 |
| B. SSH + tmux | PC / VPS + Tailscale | 中 | 高 |
| C. Termux ネイティブ | Android のみ | 中 | 中 |
| D. proot-Ubuntu | Android のみ | 高 | 中 |

---

## A. Remote Control（公式機能）

2026年2月に Anthropic がリリースした機能。PC 上で動いている Claude Code セッションを、スマホの `claude.ai/code` またはモバイルアプリから操作できる。

仕組みはシンプルで、PC 側のローカル環境はそのまま維持される。ファイルシステム・MCP サーバー・プロジェクト設定はすべて PC に残り、スマホはその「窓」として機能する。接続中も Claude はローカルで動き続けるため、クラウドに何かが移動するわけではない。

セットアップは Claude Code v2.1.51 以降で有効になる。PC でセッションを開始すると QR コードが表示され、スキャンするだけで接続できる。既存の設定を変える必要はほぼない。

制約は明確だ。PC の電源とターミナルが開いていることが前提で、1 セッションに同時接続できるのは 1 つだけ。ネットワーク復帰後はセッションが自動再接続される。

Z Fold 7 の内側ディスプレイ（約 7.6 インチ）であれば、ターミナル出力を確認しながら右半分でブラウザを表示するマルチウィンドウ構成が自然に使える。

---

## B. SSH + tmux（Tailscale 経由）

Remote Control が登場する前から実績のある方法で、安定性では今も最も信頼できる。

構成は「デスクトップ / VPS → Tailscale → Termux(Android) → SSH → tmux → Claude Code」となる。tmux を挟むことで、接続が切れても作業が保持される。移動中に Claude Code を走らせておき、目的地に着いてから続きを確認する、という使い方に合っている。

Harper Reed が「2000年代初期のプログラミング体験が戻ってきた」と書いたように、このパターンは枯れた技術の組み合わせで動作が安定している。初期セットアップに 20 分程度かかるが、以降はほぼメンテナンス不要だ。VPS を使う場合は月数百〜数千円の費用が発生する。

---

## C. Termux ネイティブ

Android 上の Termux で直接 Claude Code を動かすパターン。npm のグローバルインストールではなく、linux-arm64 バイナリを glibc-runner 経由で実行する形が現在の主流になっている。

インストール容量はバイナリ単体で約 233MB、推奨パッケージ込みで約 433MB。セットアップ時間は 5〜10 分程度と軽い。

注意が必要なのが Android 15 の Phantom Process Killer だ。バックグラウンドの長時間プロセスを強制終了するため、tmux 内で実行することが前提になる。また Java コンパイルなど重いビルド処理は現実的でない。Z Fold 7 は Snapdragon 8 Elite を積んでいるため処理性能に余裕はあるが、OS 側の制約が先に来る。

PC なしで完結させたい場面や、外出先でちょっとした確認作業をしたいときに使える。

---

## D. proot-Ubuntu

Termux 内に proot で Ubuntu 環境を構築してその中で実行するパターン。`process.platform` が `linux` を返すため、Linux 向けツールとの互換性が高い。Java や Go など複雑なビルドツールも動かせる。

容量は約 2GB 必要で起動も重い。C のネイティブ実行で制約が出る場面への対処として検討する程度でよく、最初から選ぶパターンではない。

---

## どのパターンを選ぶか

自宅に常時起動している PC があるなら、まず **A. Remote Control** を試す。セットアップが最小で公式サポートがあり、既存の開発環境をそのまま使える。

PC が常時起動していない、または外出先からも同じ環境を使いたい場合は **B. SSH + tmux** を本線にする。Tailscale の設定を一度やってしまえば、あとはどこからでもつながる。

**C. Termux ネイティブ** は補助的に持っておくと便利だ。PC が使えない状況でも、軽い作業や確認程度なら動く。

Z Fold 7 の大画面とマルチウィンドウは、どのパターンでも活きる。特に Remote Control と SSH では、ターミナルとブラウザを並べた PC に近い作業環境が作れる。

## 参考

- [Continue local sessions from any device with Remote Control — Claude Code 公式ドキュメント](https://code.claude.com/docs/en/remote-control)
- [Claude Code Mobile: iPhone, Android & SSH (2026) — Sealos Blog](https://sealos.io/blog/claude-code-on-phone/)
- [How I Use Claude Code on My Phone with Termux and Tailscale](https://www.skeptrune.com/posts/claude-code-on-mobile-termux-tailscale/)
- [GitHub - ferrumclaudepilgrim/claude-code-android](https://github.com/ferrumclaudepilgrim/claude-code-android)
- [Remote Claude Code: programing like it was the early 2000s — Harper Reed's Blog](https://harper.blog/2026/01/05/claude-code-is-better-on-your-phone/)
- [How to Use Claude Code on Mobile: Android Termux and iOS SSH Setup — BSWEN](https://docs.bswen.com/blog/2026-03-24-mobile-usage/)
