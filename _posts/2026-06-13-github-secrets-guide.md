---
layout: post
title: "GitHub Secrets で API キーを安全にワークフローへ渡す"
subtitle: "Repository Secrets と Environment Secrets の違いと使い分け"
categories: 開発
tags: ["Git", "自動化", "開発環境"]
lang: ja
---

API キーやパスワードをリポジトリに直書きしてコミットしてしまった、という話は珍しくない。GitHub Secrets はこの問題に対処するための仕組みで、GitHub Actions のワークフローから安全に機密情報を参照できるようにする。

---

## Secrets とは何か

GitHub Secrets は、ワークフロー YAML に直接書けない機密情報（API キー・アクセストークン・パスワードなど）を暗号化して保存し、ワークフロー実行時に環境変数として参照できるようにする機能だ。

保存されたシークレットは Libsodium sealed box で暗号化される。GitHub は登録済みシークレットに一致する値をワークフローログからマスクするが、変換・分割された値まで確実に隠せるとは限らない。シークレットを意図的にログへ出力しないことが前提になる。

ワークフロー内での参照方法はこうなる。

{% raw %}
```yaml
steps:
  - name: Deploy
    env:
      API_KEY: ${{ secrets.MY_API_KEY }}
    run: ./deploy.sh
```
{% endraw %}

{% raw %}`${{ secrets.シークレット名 }}`{% endraw %} で参照するだけで、YAML にキーの値が残らない。

---

## 3 種類のシークレット

GitHub のシークレットには、保存スコープが異なる 3 種類がある。

| 種類 | スコープ | 上限 |
| :--- | :--- | :--- |
| Repository Secrets | そのリポジトリのすべてのワークフロー | 100 個 |
| Environment Secrets | 特定の Environment を参照するジョブのみ | 100 個 |
| Organization Secrets | 組織内の指定リポジトリのすべてのワークフロー | 1,000 個 |

### Repository Secrets

リポジトリの **Settings → Secrets and variables → Actions** から登録する。そのリポジトリ内のすべてのワークフローから参照できる。

個人プロジェクトや小規模な用途であればここから始めて問題ない。登録・変更はシンプルで、UI から直接操作できる。

### Environment Secrets

GitHub には **Environments** という概念があり、`production` や `staging` のような単位でシークレットや保護ルールをまとめて設定できる。

Environment Secrets を参照するには、ジョブ定義に `environment:` を明示する必要がある。

{% raw %}
```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production      # この指定がないと Environment Secrets にアクセスできない
    steps:
      - name: Deploy
        env:
          DATABASE_URL: ${{ secrets.PROD_DATABASE_URL }}
        run: ./deploy.sh
```
{% endraw %}

Environment Secrets の特徴は **Deployment protection rules** を組み合わせられる点にある。Environment に必要承認者を設定すると、そのジョブが実行される前に承認が必要になる。本番デプロイのセーフティネットとして機能する。

設定場所: **Settings → Environments → （対象 Environment を選択） → Protection rules**

GitHub Free・Pro・Team では、必要承認者と待機タイマーを利用できるのはパブリックリポジトリに限られる。プライベートリポジトリで使う場合は、契約プランと利用条件を確認する必要がある。

### Organization Secrets

GitHub Organization に属するリポジトリ間で共通のシークレットを管理できる。Slack 通知用トークンや共通の Docker Hub 認証情報など、複数リポジトリで使い回すものを一箇所で管理したい場合に使う。個人アカウントのリポジトリには適用されない。

GitHub Free の Organization Secrets は、プライベートリポジトリから利用できない。Organization Secrets を設計するときは、対象リポジトリの公開範囲とプランも確認する。

---

## 同名のシークレットが複数ある場合の優先順位

同じ名前のシークレットが複数スコープに存在する場合、スコープが狭いほど優先される。

```
Environment Secrets  >  Repository Secrets  >  Organization Secrets
（最優先）                                        （最低優先）
```

Organization Secrets に `DATABASE_URL` があっても、Repository Secrets に同名のものが登録されていれば、ワークフローは Repository Secrets の値を使う。

この挙動を使うと「組織全体のデフォルト値を Organization Secrets に置き、特定リポジトリだけ上書きしたい場合は Repository Secrets で同名のものを登録する」という運用ができる。

---

## 使い分けの目安

| ケース | 向いているシークレット |
| :--- | :--- |
| 個人プロジェクト、環境を分けていない | Repository Secrets |
| 本番デプロイに承認ステップを入れたい | Environment Secrets |
| 本番と開発で異なる値を使いたい | Environment Secrets（環境ごとに登録） |
| 複数リポジトリで同じシークレットを使いたい | Organization Secrets |

個人での CI 程度であれば Repository Secrets で十分だ。チームで本番環境へのデプロイを管理する場合は、Environment Secrets と Deployment protection rules を組み合わせると誤操作への備えになる。

---

## サイズ制限と注意点

- 1 つのシークレットは最大 **48 KB**
- 48 KB を超える機密ファイルは、GPG で暗号化したファイルをリポジトリへ保存し、復号用パスフレーズだけを GitHub Secrets に登録する方法がある。AWS Secrets Manager・HashiCorp Vault のような外部サービスを使う選択肢もある
- Base64 は暗号化ではなく、エンコード後のデータサイズも増える。48 KB を超えるシークレットを収める手段にはならない
- シークレット名は英数字とアンダースコアのみ使用できる。`GITHUB_` で始まる名前は予約済みのため使えない
- フォークから起動されたワークフローには、原則として `GITHUB_TOKEN` 以外のシークレットは渡されない

---

## GitHub CLI でのシークレット操作

ブラウザを開かずにシークレットを操作したい場合は `gh` コマンドが使える。

```bash
# シークレットを設定
gh secret set MY_API_KEY

# ファイルから設定
gh secret set MY_API_KEY < ./secret.txt

# 一覧表示
gh secret list

# 削除
gh secret delete MY_API_KEY

# Environment Secrets を操作する場合は --env を指定
gh secret set PROD_API_KEY --env production
```

CI 環境のセットアップを自動化する際に便利だ。

---

## 参考

- [Using secrets in GitHub Actions - GitHub Docs](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets)
- [Secrets reference - GitHub Docs](https://docs.github.com/en/actions/reference/security/secrets)
- [Understanding GitHub secret types - GitHub Docs](https://docs.github.com/en/code-security/reference/secret-security/understanding-github-secret-types)
