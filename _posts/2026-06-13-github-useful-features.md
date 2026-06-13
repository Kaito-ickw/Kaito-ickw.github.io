---
layout: post
title: "まだ使っていない GitHub の便利機能を整理する"
categories: 開発
tags: ["Git", "自動化", "開発環境", "CLI"]
lang: ja
---

GitHub は Pull Request とブランチ管理だけでも十分使えるが、他にも実用的な機能が揃っている。知らないまま使っていないものをいくつか整理した。

---

## GitHub CLI（gh コマンド）

`gh` は GitHub 公式の CLI ツールで、ブラウザを開かずに GitHub の操作ができる。

```bash
# インストール（macOS）
brew install gh

# 認証
gh auth login
```

日常的に使うコマンドはこのあたり。

```bash
# PR を作成
gh pr create --title "fix: ログ出力の修正" --body "..."

# PR 一覧を確認
gh pr list

# PR をマージ
gh pr merge 42

# Issue を作成
gh issue create --title "バグ報告" --label bug

# ワークフローを手動実行
gh workflow run deploy.yml

# リリースを作成
gh release create v1.2.0 --generate-notes
```

特に `gh pr create` は手元のブランチから直接 PR を出せるので、ブラウザとターミナルを行き来する手間が省ける。AIエージェントにリポジトリ操作を任せるときも、`gh` を使ったコマンドとして記述しやすい。

インストール方法: [cli.github.com](https://cli.github.com)

---

## Dependabot

依存パッケージのバージョンアップや脆弱性対応の PR を自動で作ってくれる機能。有効にすると、GitHub が定期的に依存関係をスキャンして更新 PR を送ってくる。

`.github/dependabot.yml` を置くだけで有効になる。

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"    # pip / npm / bundler / docker など
    directory: "/"
    schedule:
      interval: "weekly"        # daily / weekly / monthly
    labels:
      - "dependencies"
```

2 種類の機能がある。

**Dependabot security updates** は、既知の脆弱性（CVE）が登録された依存パッケージを自動的に安全なバージョンへ更新する PR を作成する。パブリックリポジトリでは無料で使える。Settings → Security → Dependabot alerts から有効にできる。

**Dependabot version updates** は、脆弱性の有無にかかわらず最新バージョンへの更新 PR を定期的に作る。`dependabot.yml` を置いておくだけで動く。

ライブラリを手動でアップデートし忘れるパターンが減る。PR として来るのでレビューしてマージするかどうかを判断できる。

---

## Branch Protection Rules

`main` ブランチへの直接 push を防いだり、CI が通らない限りマージできないようにする設定。個人開発でも入れておくと安心できる。

**Settings → Branches → Add branch protection rule** から設定する。

よく使う設定項目:

| 設定 | 内容 |
| :--- | :--- |
| Require a pull request before merging | direct push を禁止。PR 経由でのみマージ可能にする |
| Require status checks to pass | 指定した CI ジョブが成功しないとマージできない |
| Require branches to be up to date | base ブランチに追いついていないとマージできない |
| Do not allow bypassing the above settings | 管理者でもルールを回避できないようにする |

個人リポジトリで CI を走らせている場合は「Require status checks to pass」だけでも入れておくと、テストが落ちたまま main を更新してしまうミスを防げる。

---

## Secret Scanning と Push Protection

コードにトークンや API キーを誤ってコミットしてしまうミスを防ぐ機能。

**Secret scanning** はコミット済みのコードをスキャンして、既知のシークレットパターン（GitHub トークン・AWS キーなど）を検出したら通知する。パブリックリポジトリではデフォルトで有効になっている。

**Push protection** は push 時点でシークレットが含まれていないかチェックし、含まれていれば push をブロックする。シークレットがリポジトリへ到達する前に止められる。

Push protection には、ユーザー単位とリポジトリ単位の2種類がある。ユーザー単位のPush ProtectionはGitHub.comでデフォルト有効になっており、そのユーザーがパブリックリポジトリへシークレットをpushする操作を保護する。

リポジトリ単位のPush Protectionはデフォルト無効で、GitHub Secret Protectionを有効にしたリポジトリで利用する。プライベート・内部リポジトリでのSecret scanningやPush Protectionは、Organizationのプランと設定に依存する。個人所有のプライベートリポジトリで、無料のユーザー単位Push Protectionをリポジトリ保護として利用できるわけではない。

GitHub Secrets を使ったシークレット管理については [GitHub Secrets で API キーを安全にワークフローへ渡す]({% post_url 2026-06-13-github-secrets-guide %}) も参考にしてほしい。

---

## GitHub Actions の便利な使い方

基本的な CI の設定はできていても、以下の機能を使うとさらに柔軟になる。

### workflow_dispatch（手動トリガー）

通常の CI は push や PR をトリガーにするが、`workflow_dispatch` を使うと手動で実行できる。

```yaml
on:
  workflow_dispatch:
    inputs:
      environment:
        description: "デプロイ先"
        type: choice
        options:
          - staging
          - production
        required: true
```

`gh workflow run deploy.yml -f environment=staging` のように CLI から実行できる。GitHub の UI からもパラメータを選んで実行できる。

定期的に手動で実行したいバッチ処理や、環境を選んでデプロイしたい場合に使いやすい。

### cache（依存関係のキャッシュ）

CI で毎回 `pip install` や `npm install` が走ると時間がかかる。`actions/cache` を使うと依存関係をキャッシュして次回以降の実行を速くできる。

{% raw %}
```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-
```
{% endraw %}

`key` に `requirements.txt` のハッシュを含めることで、ファイルが変更されたときに自動的にキャッシュを再作成する。

---

## Issue / PR テンプレート

Issue や PR を作成するときに、あらかじめ定めたフォーマットを表示させる機能。

```
.github/
  ISSUE_TEMPLATE/
    bug_report.md
    feature_request.md
  PULL_REQUEST_TEMPLATE.md
```

PR テンプレートの例:

```markdown
## 変更内容

## 確認事項

- [ ] テストを追加した
- [ ] ドキュメントを更新した

## 関連 Issue

Closes #
```

チームで運用するとレビューに必要な情報が揃いやすくなる。個人プロジェクトでも、後から見返したときの記録として機能する。

---

## GitHub Releases

タグを切るだけでなく、リリースノートを作成して公開できる機能。`gh release create` で CLI から作れる。

```bash
gh release create v1.2.0 --generate-notes
```

`--generate-notes` をつけると、前回のリリースから今回までのマージ済み PR を自動で列挙したリリースノートを生成してくれる。手で変更点をまとめる手間が省ける。

GitHub の Releases ページが生成され、タグに対応するバイナリやソースの zip もアタッチできる。OSS として公開するプロジェクトや、バージョン管理が必要なツールを配布する場合に使いやすい。

---

## まとめ

| 機能 | 主な使いどころ | 設定場所 |
| :--- | :--- | :--- |
| GitHub CLI | ブラウザ不要で PR・Issue・ワークフロー操作 | `brew install gh` |
| Dependabot | 依存パッケージの自動更新・脆弱性対応 | `.github/dependabot.yml` |
| Branch Protection | main への直接 push 禁止・CI 必須化 | Settings → Branches |
| Secret Scanning | コミット済みシークレットの検出 | デフォルト有効（public） |
| Push Protection | push 前にシークレット混入をブロック | ユーザー単位はpublicでデフォルト有効 |
| workflow_dispatch | ワークフローの手動・パラメータ付き実行 | YAML に `on: workflow_dispatch` |
| cache | CI の依存インストールを高速化 | `actions/cache@v4` |
| Issue/PR テンプレート | 記録・レビューのフォーマット統一 | `.github/` 以下に配置 |
| GitHub Releases | タグとリリースノートの公開 | `gh release create` |

いずれも GitHub 上で完結する機能で、追加のサービスは不要だ。一度設定すれば自動で動くものが多いので、使っていないものから順に試してみるといい。

---

## 参考

- [GitHub CLI - cli.github.com](https://cli.github.com)
- [Dependabot quickstart guide - GitHub Docs](https://docs.github.com/en/code-security/tutorials/secure-your-dependencies/dependabot-quickstart)
- [About secret scanning - GitHub Docs](https://docs.github.com/en/code-security/secret-scanning/introduction/about-secret-scanning)
- [About push protection - GitHub Docs](https://docs.github.com/en/code-security/secret-scanning/introduction/about-push-protection)
- [Workflow syntax for GitHub Actions - GitHub Docs](https://docs.github.com/actions/using-workflows/workflow-syntax-for-github-actions)
