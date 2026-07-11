---
layout: post
title: "AIエージェント前提のターミナル Herdr と cmux"
subtitle: Herdr と cmux が解決するマルチエージェント運用の課題
categories: AI開発
tags: ["AIエージェント", "マルチエージェント", "コーディングエージェント", "Claude Code", "Codex", "自動化", "CLI", "OSS", "Herdr", "cmux"]
lang: ja
image:
  path: /assets/images/posts/2026-07-11-ai-agent-terminal-herdr-cmux/eyecatch.png
  alt: "並んだ複数の作業ブースのうち一つだけ静止し、そのブースだけに橙色の光る枠が灯って目立っているリソグラフ風のイラスト"
---

Claude CodeやCodex CLIを1つのターミナルで動かすだけなら、これまでのtmuxやiTerm2で十分だった。ただ、複数のエージェントを同時に走らせて、片方が入力や承認待ちで止まっている間にもう片方の作業を見る、という運用が当たり前になると事情が変わってくる。tmuxのペインはエージェントの状態を知らないので、どのペインが人の入力を待っているかは自分の目で探すしかない。

この隙間を埋めるツールとして、2026年に入ってHerdrとcmuxという2つのターミナルが登場した。どちらも「AIエージェントが端末を使うこと」を前提に設計されている点が共通する。本記事ではこの2つを軸に、AIエージェント前提のターミナルというカテゴリが何を解決しようとしているのかを整理する。

> 本記事のバージョン・スター数・ライセンス情報は2026年7月11日に各公式サイト・GitHubリポジトリで確認した内容である。両ツールとも開発が速く、数週間で仕様が変わる可能性がある。

---

## 何が「AIエージェント前提」を定義するか

既存のターミナルマルチプレクサ（tmux、Zellijなど）は、プロセスが人間のシェルであることを前提に設計されている。ペインは単なる画面の分割で、中で動いているプロセスが「作業中」なのか「入力待ち」なのかをターミナル側は関知しない。

HerdrとcmuxはいずれもClaude Code、Codex、OpenCode、Gemini CLIなど、ターミナルで動くエージェントを前提に、複数エージェントをタブやペインで並行管理し、入力待ちのペインを通知やハイライトで知らせるという問題意識を共有している。ただし状態を知る仕組みは同じではない。Herdrはプロセスそのものを監視して状態を自動識別するのに対し、cmuxは通知シーケンスやフックを介してエージェント側から状態を伝える方式を取る。以下、それぞれの実装を見ていく。

---

## Herdr: tmuxを置き換える、エージェント検知付きの多重化ツール

[Herdr](https://herdr.dev/)は「one terminal for the whole herd」を謳う、Rust製のエージェント用ターミナルマルチプレクサである。tmuxのペイン・タブ・セッション永続化のモデルを踏襲しつつ、動いているプロセスをエージェントとして自動識別し、working・idle・blockedといった状態をサイドバーに表示する。

見た目や操作感はtmuxに近く、既存のWezTerm、iTerm2、Kittyなど手元のターミナルの中でHerdrというプロセスを起動する形になる。cmuxのような専用GUIアプリではなく、あくまでターミナル内で完結するTUIというのが立ち位置だ。

主な特徴は次のとおり。

- セッションが端末を閉じても生き続け、SSH経由で同じ永続セッションへどこからでも再接続できる
- 15種類以上のエージェントを追加設定なしで検知する（Claude Code、GitHub Copilot CLI、Codexなどが対象）
- CLIとJSONソケットAPIを備え、通知フックなど外部の自動化と連携できる

開発はRustで、AGPL-3.0-or-laterのオープンソース版と、組織向けの商用ライセンスを併用するデュアルライセンス方式を取っている。2026年7月11日時点でGitHubスター数は15.3k、最新リリースはv0.7.3（2026年7月7日）。インストールは`curl -fsSL https://herdr.dev/install.sh | sh`で行う（Windows版はベータ扱い）。

すでにtmuxやSSH経由のリモート開発に慣れているなら、操作感を変えずにエージェント検知だけ足す選択として合っている。

---

## cmux: Ghosttyベースの、AIエージェント運用を前提にしたmacOSネイティブターミナル

[cmux](https://cmux.com/)（[GitHubリポジトリ](https://github.com/manaflow-ai/cmux)）は、Ghosttyのレンダリングエンジンであるlibghosttyを使い、Manaflow AIがSwift + AppKitで組み上げたmacOS専用のネイティブアプリである。Ghosttyのフォークではなく、レンダリング部分を利用した別アプリという位置づけになる。tmuxのようにターミナルの中で動くツールではなく、cmux自体がターミナルアプリそのものという点がHerdrと異なる。

サイドバーには縦型タブが並び、各ワークスペースのgitブランチ、紐づくPRのステータス、待ち受けポート、直近の通知内容が表示される。エージェントが入力を待っている間はペインの枠に青いリングが表示され、該当タブも点灯する。

cmux独自の機能として次の2つが目立つ。

- **Embedded Browser**: ターミナルの隣にブラウザペインを分割表示できる。ナビゲーション、DOM取得、クリック、入力、JavaScript実行をプログラムから操作でき、エージェントが自分の変更したWebページをその場で確認できる
- **Claude Code Teamsのペイン可視化**: `cmux claude-teams`により、Claude Codeのteammateモードでサブエージェントが生成された際、それらを隠れたバックグラウンドプロセスではなく、可視化されたネイティブのペイン・分割として扱う

対応エージェントはClaude Code、Codex、OpenCode、Gemini CLIなど、ターミナルから起動できるものであれば基本的に動く。ライセンスはGPL-3.0-or-later、開発元はManaflow AI。2026年7月11日時点でGitHubスター数は24.2k、最新リリースはv0.64.17（2026年6月23日）。インストールはDMG配布のほか、`brew tap manaflow-ai/cmux && brew install --cask cmux`で行える。無料・オープンソースで、Herdrと同様に組織向けの商用ライセンスも別途用意されている。加えて、開発を支援し早期アクセスを受けたい個人向けに「cmux Founders Edition」という支援プランがある（これはライセンス形態ではなく有償プラン）。

macOSを使っていて、リッチなGUIとブラウザ連携込みでエージェント運用を可視化したいなら、cmuxの方が体験として作り込まれている。ただし現状はmacOS専用で、Linux・Windows・Android対応はウェイトリスト段階にとどまる。

---

## Herdrとcmuxの比較

| 観点 | Herdr | cmux |
| :--- | :--- | :--- |
| 形態 | 既存ターミナル内で動くTUI（tmux型） | Ghostty基盤のネイティブGUIアプリ |
| 対応OS | macOS・Linux（安定）、Windows（ベータ） | macOSのみ（他OSはウェイトリスト） |
| 実装言語 | Rust | Swift |
| リモート利用 | SSH経由で永続セッションへ再接続 | SSHリモートワークスペースへ接続 |
| 特徴的な機能 | JSONソケットAPI、15種以上のエージェント自動検知 | Embedded Browser、Claude Code Teamsのペイン可視化 |
| ライセンス | AGPL-3.0-or-later（無料）+ 組織向け商用ライセンス | GPL-3.0-or-later（無料）+ 組織向け商用ライセンス |
| スター数（2026-07-11時点） | 15.3k | 24.2k |

どちらもtmux的な「複数の作業を同時に見る」発想を、人間ではなくエージェントの状態に合わせて再設計した点は共通している。違いは、既存のターミナル資産を活かすか（Herdr）、ターミナルごと置き換えてネイティブアプリの体験を取るか（cmux）という設計判断にある。

---

## 周辺で広がるエージェント多重化ツール群

HerdrとcmuxはAIエージェント前提ターミナルという新しいカテゴリの中でも代表格だが、同時期に類似のツールもいくつか登場している。[amux](https://github.com/mixpeek/amux)はクラッシュしたエージェントを自動検知して復旧させるウォッチドッグ機能とWebダッシュボード・モバイル通知を備え、tmuxの上にエージェント制御プレーンを重ねるツールとして紹介されている。[dmux](https://github.com/standardagents/dmux)はGit worktreeによる作業分離に特化し、1コマンドで複数エージェントへタスクを振り分けるtmuxペインマネージャーである。cmuxのWindows移植を掲げる[wmux](https://github.com/amirlehmam/wmux)のようなプロジェクトも出てきている。

なお「amux」という名称は本記事で参照したmixpeek/amux以外にも同名の別プロジェクトが複数存在する。このカテゴリ自体が命名も含めてまだ流動的であることの表れでもあるので、導入時はリポジトリのオーナーとURLを取り違えないよう確認したい。上記の比較記事はamux.io自身によるものであり、他ツールとの比較は一次情報というより参考情報として扱うのがよい。

---

## まとめ

tmuxやiTerm2でも複数のAIエージェントを並行して動かすこと自体はできる。HerdrとcmuxはそこにAIエージェント特有の状態管理を組み込み、「どのエージェントが今止まっているか」を探す手間を減らすことに重点を置いたツールだ。既存のターミナル運用を変えたくないならHerdr、macOSでネイティブアプリの体験ごと刷新したいならcmuxが候補になる。

## 参考

- [Herdr公式サイト](https://herdr.dev/)
- [Herdr ドキュメント](https://herdr.dev/docs/)
- [ogulcancelik/herdr - GitHub](https://github.com/ogulcancelik/herdr)
- [cmux公式サイト](https://cmux.com/)
- [manaflow-ai/cmux - GitHub](https://github.com/manaflow-ai/cmux)
- [cmux: The Native macOS Terminal Built for Running AI Coding Agents in Parallel - DEV Community](https://dev.to/arshtechpro/cmux-the-native-macos-terminal-built-for-running-ai-coding-agents-in-parallel-52il)
- [Best AI Agent Multiplexers Compared (2026): 12 Tools Ranked — amux](https://amux.io/guides/best-ai-agent-multiplexers-2026/)
- [mixpeek/amux - GitHub](https://github.com/mixpeek/amux)
- [standardagents/dmux - GitHub](https://github.com/standardagents/dmux)
- [amirlehmam/wmux - GitHub](https://github.com/amirlehmam/wmux)
