---
layout: post
title: "Git submodule と Git subtree の違いと使い分け"
subtitle: 外部リポジトリを取り込む2つの方法を比較する
categories: 開発
tags: ["Git", "開発環境", "CLI"]
lang: ja
---

外部のリポジトリを自分のプロジェクトに組み込みたいとき、Git には `submodule` と `subtree` という2つのアプローチがある。どちらも「外部リポジトリを取り込む」ことはできるが、仕組みも運用上の扱いも大きく異なる。

この記事では、それぞれの仕組みを整理し、どういう状況でどちらを選ぶかを考える。

---

## Git submodule とは

submodule は、外部リポジトリへの「参照」を親リポジトリに持たせる仕組みだ。実体のコードは外部リポジトリ側にあり、親リポジトリは「どのリポジトリの・どのコミットを使うか」という情報だけを持つ。

```
my-project/
├── .gitmodules       ← submoduleの設定ファイル
├── src/
└── libs/
    └── external-lib/ ← submoduleとして登録したディレクトリ
```

`.gitmodules` にはリポジトリURLとパスが記録され、`libs/external-lib/` ディレクトリ自体はコミットハッシュへのポインタとして扱われる。

### 基本的なコマンド

```bash
# submoduleを追加する
git submodule add https://github.com/org/external-lib libs/external-lib

# リポジトリをクローンする（submoduleも含めて）
git clone --recurse-submodules https://github.com/me/my-project

# すでにクローン済みのリポジトリでsubmoduleを初期化・取得する
git submodule update --init --recursive

# submoduleを最新コミットに追従させる
git submodule update --remote
```

### submodule を使う際の注意点

submodule を含むリポジトリをクローンした直後は、`libs/external-lib/` ディレクトリが空になっている。`git submodule update --init` を実行して初めてコードが取得される。これを忘れると「ファイルがない」という状況に陥る。

もう一つの特性は、submodule が「どのコミットを指しているか」を親リポジトリが管理するという点だ。外部ライブラリ側で新しいコミットが積まれても、親リポジトリは古いコミットを指したままになる。意図的な固定とも言えるが、更新を取り込むには明示的な操作が必要になる。

---

## Git subtree とは

subtree は、外部リポジトリのコードを親リポジトリの歴史の中に直接取り込む仕組みだ。取り込んだ後は、外部リポジトリへの依存関係はなくなり、ただのディレクトリとして扱われる。

```bash
# subtreeとして追加する
git subtree add --prefix=libs/external-lib \
  https://github.com/org/external-lib main --squash

# 外部リポジトリの更新を取り込む
git subtree pull --prefix=libs/external-lib \
  https://github.com/org/external-lib main --squash

# 変更を外部リポジトリへ送り返す
git subtree push --prefix=libs/external-lib \
  https://github.com/org/external-lib main
```

`--squash` をつけると外部リポジトリのコミット履歴を1つにまとめてから取り込む。外部の細かいコミット履歴を親リポジトリに持ち込みたくない場合は `--squash` を使うことが多い。

### subtree の特徴

クローンした人が何も意識しなくてよいのが大きな利点だ。`git clone` だけで完結する。submodule のように「初期化を忘れた」という問題が起きない。

一方、`--squash` なしで使うとコミット履歴が混在して見づらくなる。また、取り込んだコードに変更を加えて元のリポジトリへ送り返す（`subtree push`）操作はやや複雑で、Gitの知識が必要になる。

---

## どちらを選ぶか

| | submodule | subtree |
| :--- | :--- | :--- |
| 外部リポジトリとの連動 | 強い（コミット単位で追従） | 弱い（pullで手動取り込み） |
| クローン後の手順 | `submodule update` が必要 | 不要 |
| チームへの負担 | 大きい（全員がsubmoduleを理解する必要） | 小さい |
| 外部リポジトリへの書き戻し | 難しくない | やや複雑 |
| 履歴の扱い | 外部の履歴は外部にある | 親に取り込まれる |

選び方の目安は次の通り。

**submodule が向いている場面**

- 外部リポジトリを特定のコミットに固定して使いたい（ライブラリのバージョン固定）
- 外部リポジトリへの変更を頻繁に送り返す
- チーム全員がGitの扱いに慣れている

**subtree が向いている場面**

- チームに Git 初心者がいる、または外部ツールが submodule に対応していない
- 取り込んだコードをそのまま使い、ほとんど更新しない
- シンプルなワークフローを優先する

実際のところ、ソロ開発や小規模チームでは subtree の方が扱いやすいケースが多い。submodule は「外部リポジトリとの同期を密にしたい」という明確な理由がある場合に選ぶ方が、運用上の混乱が少ない。

---

## よくある混乱を整理する

### 「submodule を追加したのにコードがない」

`git clone` 後に `git submodule update --init --recursive` を実行していないことが原因だ。`--recurse-submodules` つきでクローンすれば一発で済む。

### 「submodule のバージョンを上げたら他のメンバーでビルドが通らなくなった」

submodule のコミットポインタを更新した後、`git submodule update` を実行してもらう必要がある。これを徹底するのが難しい場合は、READMEに手順を明記するか、subtree への移行を検討する。

### 「subtree pull でコンフリクトが大量に出た」

`--squash` の有無を途中で変えるとコンフリクトが起きやすい。最初に決めた方針を最後まで貫くことが重要だ。

---

## まとめ

| 観点 | submodule | subtree |
| :--- | :--- | :--- |
| 仕組み | 外部リポジトリへの参照 | 外部リポジトリの歴史を直接取り込む |
| 独立性 | 低い（外部リポジトリに依存） | 高い（取り込んだら独立） |
| 扱いやすさ | 慣れが必要 | 直感的 |
| 用途 | バージョン固定・頻繁な同期 | シンプルな取り込み・ほぼ読み取り専用 |

どちらが優れているという話ではなく、用途と状況によって使い分けるものだ。迷ったら subtree から始めて、「外部リポジトリとの同期をもっと細かく管理したい」という必要が出てきたときに submodule を検討するのが現実的な順序だと思う。
