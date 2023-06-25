---
layout: post
title: "JekyllとGitHub Pagesを使ったブログサイトの記事更新手順"
subtitle: 記事更新を効率化する
categories: ブログ
tags: ["GitHub Pages","Jekyll"]
---

このサイトでは、Jekyllというツールを使ってブログ記事を作成しています。
手順はとてもシンプルで、Markdown形式で記事を作成し、ローカル環境で確認したら、GitHubにアップロードするだけです。
GitHub Actionによって自動的にビルドが行われ、サイトが更新されます。

手順を覚えてしまえば、誰でも簡単にブログ記事をアップできるようになります。
詳しい手順は以下の通りです。

1. **Markdown形式で記事を執筆:** 
まずは新しい記事をMarkdown形式で書きます。
Jekyllの場合、通常_postsフォルダの中に`yyyy-mm-dd-title.md`という形式でファイルを作成します。
ここで、`yyyy-mm-dd`は記事の公開日、`title`は記事のタイトルを示しています。
この.mdファイルの先頭には、Jekyllが解析するためのYAML形式のFront Matterを記述します。

例えば、以下のような形です。

```
---
layout: post
title:  "記事のタイトル"
subtitle: "記事のサブタイトル"
categories: カテゴリ
tags: [タグ1, タグ2]
---
```

2. **ローカル環境でJekyll Serverを起動:** 
次に、ローカル環境でJekyllのサーバーを立ち上げて、記事の表示を確認します。
コマンドラインでサイトのルートディレクトリに移動し、`bundle exec jekyll serve`コマンドを実行します。これにより、Jekyllのサーバーが起動し、ローカル環境の`localhost:4000`でサイトを確認できるようになります。

3. **ページ表示の確認:** 
ブラウザで`localhost:4000`にアクセスし、新しい記事が正しく表示されていることを確認します。
レイアウトや文字の表示、リンクの動作などを一通り確認します。

4. **コミットとプッシュ:** 
記事の確認が完了したら、変更をGitでコミットし、GitHubのリポジトリにプッシュします。
以下のコマンドを実行します。

```
git add .
git commit -m "新しい記事を追加"
git push origin master
```

5. **GitHub Actionで自動ビルド:** 
GitHubにプッシュすると、特に設定不要でGitHub Actionによって自動的にビルドが始まります。
ビルドが完了すると、自動的にGitHub Pagesのサイトが更新されます。
このビルドの進行状況や結果は、GitHubのリポジトリ内の「Actions」タブで確認ができます。


以上が、JekyllとGitHub Pagesを用いたブログサイトの記事更新手順です。