---
layout: post
title: "チーム開発のブランチ戦略と Git Flow の使いどころ"
subtitle: feature・develop・release・hotfix ブランチの役割と運用の流れ
categories: 開発
tags: ["Git", "開発環境", "CLI"]
lang: ja
---

Git を使い始めると早い段階でぶつかるのが「ブランチをどう管理するか」という問題だ。一人で作業しているうちはメインブランチだけで済んでいたものが、複数人で開発するようになった途端に「誰の変更がどこにあるか」「本番に出していいコードはどれか」が不明確になる。

Git Flow はそのブランチ管理を整理するための設計の一つだ。2010年に Vincent Driessen が提案したモデルで、今も多くのチームで参考にされている。

---

## Git Flow の全体像

Git Flow が定義するブランチは大きく2種類に分かれる。**常に存在し続けるメインブランチ**と、**作業のために一時的に作る補助ブランチ**だ。

```
main       ─── 本番リリース済みのコード
develop    ─── 次のリリースに向けた統合ブランチ
```

```
feature/*  ─── 機能開発
release/*  ─── リリース準備
hotfix/*   ─── 本番の緊急修正
```

この5種類のブランチに役割を割り当てることで、「どのコードが今どの状態か」が把握しやすくなる。

---

## メインブランチ: main と develop

`main` には本番環境にデプロイ済みのコードだけが入る。直接コミットはせず、リリース時にのみ更新する。

`develop` は日々の開発の中心になるブランチだ。各機能開発が終わるたびにここへマージされ、次のリリースに向けて変更が積み重なっていく。

```bash
# リポジトリの初期設定
git init
git checkout -b develop
```

プロジェクト開始時に `develop` ブランチを切っておき、開発者はここを起点に作業ブランチを派生させる。

---

## feature ブランチ: 機能開発の単位

新機能を追加するときは `develop` から `feature` ブランチを切る。

```bash
# developから派生させる
git checkout develop
git checkout -b feature/user-authentication

# 作業が終わったらdevelopへマージ
git checkout develop
git merge --no-ff feature/user-authentication
git branch -d feature/user-authentication
```

`--no-ff` をつけると Fast-forward マージを行わず、マージコミットが残る。「どの機能をいつマージしたか」が履歴に残るため、後からの追跡が楽になる。

feature ブランチは `develop` にマージしたら削除する。ブランチが増え続けると管理が煩雑になるので、作業が完了した時点でこまめに消す習慣をつけた方がよい。

---

## release ブランチ: リリース準備の分離

機能開発が一通り終わり、次のリリースに向けて準備をする段階で `release` ブランチを切る。

```bash
git checkout develop
git checkout -b release/1.2.0
```

このブランチでやることはバグ修正・バージョン番号の更新・ドキュメントの整備など、リリース直前の細かい調整だ。新機能の追加はここでは行わない。

リリース準備が整ったら、`main` と `develop` の両方にマージする。

```bash
# mainへマージしてタグを打つ
git checkout main
git merge --no-ff release/1.2.0
git tag -a 1.2.0

# developにも反映する
git checkout develop
git merge --no-ff release/1.2.0

# ブランチを削除
git branch -d release/1.2.0
```

`develop` へのマージを忘れると、release ブランチで修正したバグが次の開発サイクルに反映されないので注意が必要だ。

---

## hotfix ブランチ: 本番の緊急対応

本番環境で問題が発覚したとき、`develop` の状態を無視して `main` から直接修正ブランチを切るのが `hotfix` だ。

```bash
git checkout main
git checkout -b hotfix/login-bug-fix

# 修正後
git checkout main
git merge --no-ff hotfix/login-bug-fix
git tag -a 1.2.1

git checkout develop
git merge --no-ff hotfix/login-bug-fix

git branch -d hotfix/login-bug-fix
```

release ブランチと同様に、`main` と `develop` の両方へマージする。`develop` にも入れないと、次のリリースで同じバグが再発する。

---

## ブランチの命名規則

Git Flow を使う場合、ブランチ名に一定のプレフィックスをつけるのが一般的だ。

| ブランチ種別 | 命名例 |
| :--- | :--- |
| feature | `feature/user-login`, `feature/csv-export` |
| release | `release/1.2.0`, `release/2026-06` |
| hotfix | `hotfix/null-pointer-fix`, `hotfix/security-patch` |

`git-flow` というCLIツールを使うと、このブランチ作成・マージ・削除の一連の操作をコマンド一つで実行できる。

```bash
# git-flowの初期化
git flow init

# featureブランチを開始
git flow feature start user-authentication

# featureブランチを完了（developへマージして削除）
git flow feature finish user-authentication
```

手動でやると手順を忘れがちな操作を自動化してくれるので、チームに慣れていないメンバーがいる場合は導入を検討してもよい。

---

## GitHub Flow との比較

Git Flow はブランチの種類が多く、全体の流れが複雑に見える。そのため「シンプルすぎる」「重い」という声もある。GitHub が採用している GitHub Flow はこれを大幅に簡略化したモデルだ。

| | Git Flow | GitHub Flow |
| :--- | :--- | :--- |
| メインブランチ | main + develop | main のみ |
| リリースの概念 | あり（release ブランチ） | なし（mainがそのままリリース） |
| 緊急修正 | hotfix ブランチ | 通常の feature と同じ扱い |
| 向いているプロジェクト | バージョン管理が明確なもの | 継続デプロイ・SaaS 系 |

バージョンを明示してリリースするタイプのソフトウェア（モバイルアプリ・ライブラリ・パッケージなど）は Git Flow が合いやすい。一方、本番環境へ随時デプロイしていく Web サービスは GitHub Flow の方がシンプルで回しやすい。

---

## 実際の運用で気をつけること

### develop の肥大化

機能開発が次々とマージされても、リリースタイミングがなかなか来ないと `develop` に大量の変更が溜まっていく。「いつリリースするか」の基準を決めておかないと、release ブランチを切るタイミングが曖昧になる。

### hotfix のマージ忘れ

`main` にマージして安心してしまい、`develop` へのマージを忘れるのがよくあるミスだ。チェックリストや CI でこれを確認する仕組みがあると安全だ。

### feature ブランチの長期放置

複数人で開発していると、ある feature ブランチが長期間 `develop` から乖離し、いざマージしようとするとコンフリクトが大量に出るという状況になりやすい。ブランチを小さく分割して短期間でマージする習慣が、Git Flow のモデルに関係なく重要だ。

---

## まとめ

Git Flow が提供するのはブランチの役割分担の設計だ。「このコードは開発中」「これはリリース準備」「これは本番対応」という状態の分離を、ブランチ構造として明示する。

複雑に見えるが、基本は「develop で開発を積み上げて、release で出荷準備をして、main が本番」という単純な流れだ。hotfix はその例外処理として `main` から直接入るだけで、覚えるパターン自体は多くない。

チームの規模や開発サイクルに合っているかどうかを確認した上で採用するのが現実的だ。CI/CD が整備されていてほぼ毎日デプロイするような環境なら、GitHub Flow の方がオーバーヘッドが少なく合いやすい。

---

## 参考

- [A successful Git branching model (Vincent Driessen)](https://nvie.com/posts/a-successful-git-branching-model/)
- [git-flow cheatsheet](https://danielkummer.github.io/git-flow-cheatsheet/)
- [GitHub Flow](https://docs.github.com/en/get-started/using-github/github-flow)
