---
layout: post
title: "「Beast モード」でAIはどこまで変わるか"
categories: AI開発
tags: ["Claude", "Claude Code", "LLM", "AIエージェント", "コーディングエージェント", "GitHub Copilot"]
lang: ja
---

「Beast モードで試してみたら全然違った」という話を見かけることがある。何かが劇的に改善した、というニュアンスで使われているが、実体を調べると「モデルを強化する機能」ではなく「エージェントの行動を変えるプロンプト」だとわかる。

---

## Beast Mode の実体

Beast Mode は、GitHub の Burke Holland が作った VS Code Copilot 向けのカスタムチャットモードだ。`.chatmode.md` というファイルに書かれた指示のセットで、現在のバージョンは 3.1。

重要なのは「モデルを変える」のではなく「エージェントの振る舞いを変える」という点だ。GPT-4.1 向けに設計されているが、どのモデルでも動く、と説明されている。つまり中身はシステムプロンプトだ。

---

## プロンプトが変える3つのこと

Beast Mode のプロンプトを読むと、大きく3つのことをやっている。

**1. 途中で止まらない**

通常のエージェントは途中で「どうしますか？」と確認を求めたり、問題が解決しないまま返答したりすることがある。Beast Mode は「問題が完全に解決されるまでターンを終了してはならない」と明示的に指示する。

```
You MUST iterate and keep going until the problem is solved.
Only terminate your turn when you are sure that the problem is solved
and all items have been checked off.
```

**2. 必ずインターネットで調べる**

「知識のカットオフがあるため、ライブラリや依存パッケージの使い方は毎回 Google で検索して確認しなければならない」という指示が入っている。インストールするたびに最新ドキュメントを fetch するよう求める。これは LLM の古い知識で動くのではなく、実際の最新情報を使わせるための仕組みだ。

**3. Todo リストで進捗を管理する**

タスクを Markdown の Todo リスト形式で分解し、完了したものを随時チェックオフしながら進める。「次は何をするか」を常に明示することで、長い作業でもどこにいるかが把握できる。

---

## VS Code への入れ方

1. VS Code の Copilot チャットサイドバーで「agent」ドロップダウンを開く
2. 「Configure Modes」を選択
3. 「Create new custom chat mode file」→「User Data Folder」
4. 名前を「Beast Mode」にする
5. Gist のプロンプトをファイルに貼り付ける

設定ファイルにも2行追加することが推奨されている。

```json
"chat.tools.autoApprove": true,
"chat.agent.maxRequests": 100
```

`autoApprove` はエージェントがターミナルコマンドを確認なしに実行できるようにするもので、`maxRequests` は長いタスクで途中に確認ダイアログが出ないようにする。この2つで、エージェントが止まらずに動き続ける環境を作る。

---

## Claude Code との違い

同じ「エージェントに自律的に動かせる」という目的だが、アプローチが違う。

Claude Code はエージェント動作がデフォルトで、ユーザーが止めない限り動き続ける設計になっている。VS Code の Copilot は Ask / Edit / Agent という段階的な構成で、Beast Mode はその Agent モードに「止まるな、調べろ、テストしろ」という行動指針をプロンプトで上乗せする形だ。

設計思想としては、[ハーネスエンジニアリング]({% post_url 2026-06-08-harness-engineering-guide %})で取り上げた「どう動かすかの制御をどこに書くか」という問題への答えが異なる。Claude Code はツール側で制御する、Beast Mode はプロンプトで制御する、ということになる。

---

## 「Beast モード」という言葉の広がり

Burke Holland の実装が広まった結果、「Beast モード的な使い方」を指す言葉としても使われるようになった。Claude Code での `ultrathink` キーワード（応答前に多くのトークンを使って考えるモード）や、OpenAI の推論モデル（o1/o3 系）をこの文脈で語ることもある。

ただしそれらは「より多く考える」モードであり、Beast Mode の「止まらず調べ続ける」とは別のアプローチだ。目指しているものは近いが、どこにレバーがあるかが違う。

---

## 参考

- [Beast Mode Gist by Burke Holland](https://gist.github.com/burkeholland/88af0249c4b6aff3820bf37898c8bacf) — Beast Mode 3.1 本体とインストール手順
- [GitHub Copilot Custom Chat Modes](https://docs.github.com/en/copilot/customizing-copilot/using-custom-chat-modes) — VS Code でのカスタムモード設定ドキュメント
- [Extended Thinking](https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking) — Claude の拡張思考（`ultrathink`）の公式ドキュメント
