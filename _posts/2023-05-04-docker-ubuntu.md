---
layout: post
title: "DockerでUbuntuを動かそう！"
subtitle: Dockerを使ったUbuntu環境の構築方法
categories: Docker
tags: [Docker, Ubuntu]
---

今回はDocker初心者の方向けに、DockerでUbuntuを動かす方法について解説します。この記事を読むことで、Dockerの基本コマンドを習得し、DockerからのUbuntu環境の構築ができるようになります。

## 概要

Dockerは、アプリケーションをコンテナ化することで、環境依存性を排除し、開発・運用の効率化を図ることができます。また、Dockerコンテナは軽量であるため、仮想マシンよりも高速に起動することができます。

## Dockerのインストール

まずは、Dockerをインストールしましょう。以下のコマンドを実行してください。

```
$ sudo apt-get update
$ sudo apt-get install docker.io
```

これで、Dockerがインストールされました。

## Ubuntuの起動

次に、DockerからUbuntuを起動してみましょう。以下のコマンドを実行してください。

```
$ sudo docker run -i -t ubuntu /bin/bash
```

これで、Dockerコンテナ内でUbuntuが起動しました。あとは、通常のUbuntuと同じように操作することができます。

## Dockerコマンドの基本

Dockerコンテナを操作するためには、Dockerコマンドを使います。ここでは、基本的なDockerコマンドを紹介します。

### コンテナの一覧表示

```
$ sudo docker ps -a
```

### Ubuntuのイメージをダウンロード

```
$ docker pull ubuntu
```

### コンテナの起動

```
$ sudo docker start [コンテナ名]
```

### コンテナの停止

```
$ sudo docker stop [コンテナ名]
```

### コンテナの削除

```
$ sudo docker rm [コンテナ名]
```

## まとめ

いかがでしたでしょうか。今回は、Docker初心者の方向けに、DockerでUbuntuを動かす方法について解説しました。Dockerコンテナを使えば、環境依存性を排除し、開発・運用の効率化を図ることができます。ぜひ、実際に手を動かして、Dockerの使い方をマスターしてください！
