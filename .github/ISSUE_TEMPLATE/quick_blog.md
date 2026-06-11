---
name: "Quick blog draft"
about: "AIとの会話やメモを貼って、ブログ記事ドラフトを作成する"
title: "[Quick Blog] "
labels: ["blog", "draft", "quick"]
---

## 依頼

<!-- 例: Claude Codeのスマホ運用について知りたいので、わかりやすく記事にまとめて -->

## 参考

<!-- ChatGPT / Claude / Gemini の共有リンク、会話コピペ、メモなどを雑に貼る -->

## 補足

<!-- 任意。想定読者、入れたい観点、避けたい内容などがあれば書く -->

## エージェントへの指示

@claude /quick-blog

この記事化してください。

* AGENTS.mdに従ってGitHub Pages用の記事ドラフトを作る
* 入力が雑でも、文脈を補って記事構成を作る
* 明らかに不足している情報があれば質問する
* ただし、細かい不明点は仮定して進める
* 社内情報、個人情報、未公開情報は一般化または除外する
* 新しいbranchを作成する
* 記事ファイルをcommitする
* remote branchへpushする
* Pull Requestを作成する
* PR本文には、記事の狙い、変更ファイル、確認ポイント、Jekyll Build確認状況を書く
* PRを作成したら、このIssueにPR URLをコメントする
* 公開前にレビューできるよう、mainへ直接pushしない
