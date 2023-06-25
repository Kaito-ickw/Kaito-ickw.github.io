---
layout: post
title: DockerでSQLサーバを構築する(仮)
subtitle:
categories: example
tags: [Docker, sql]
---

SQLパズルを読み始めたところ、実際にSQLを試す環境が欲しくなり、DockerでSQL Server構築をしてみることにしました。

## SQLパズル

SQLパズルとは、SQLを用いて問題を解決するパズルのような形式をとっています。
SQL初心者から上級者まで幅広く楽しめる内容になっていると感じました。

- [SQLパズル](https://amzn.to/3CKeFZ0)

## DockerでSQL Server構築

Dockerを使用することで、手軽にSQL Serverを構築することができます。
また、Docker Composeを使用することで、SQL Serverの設定も簡単に行うことができます。
今回は、以下のような設定でSQL Serverを構築しました。

```yaml
version: '3.7'
services:
  db:
    image: mcr.microsoft.com/mssql/server:2019-latest
    environment:
      SA_PASSWORD: "YourStrong!Passw0rd"
      ACCEPT_EULA: "Y"
    ports:
      - "1433:1433"
```

以上の設定で、Docker Composeを実行することでSQL Serverが起動します。
また、ポートフォワーディングにより、ホストマシンからもアクセス可能です。

SQL ServerをDockerコンテナとして実行する場合、ホストマシンからアクセスするためには、ポートフォワーディングが必要です。

ポートフォワーディングとは、Dockerコンテナ内で起動されているアプリケーションのポートを、ホストマシンのポートに転送することです。具体的には、Dockerコンテナ内でSQL Serverが使用するポート(デフォルトは1433番)を、ホストマシンの任意のポートに転送します。

例えば、以下のようなDockerコマンドを使用してSQL Serverを起動した場合、ホストマシンのポート8888番にSQL Serverのポート1433番を転送することができます。

```
docker run -d -p 8888:1433 --name sql_server_container -e 'ACCEPT_EULA=Y' -e 'SA_PASSWORD=YourStrong!Passw0rd' microsoft/mssql-server-linux
```

この場合、ホストマシンからSQL Serverにアクセスする際には、以下の接続文字列を使用します。

```
Server=localhost,8888;Database=mydatabase;User Id=sa;Password=YourStrong!Passw0rd;
```

こうすることで、ホストマシンからもSQL Serverにアクセスすることができます。


SQL Serverを構築したら、次に実際にSQLを実行する手順が必要です。以下の手順で進めてみましょう。

1. SQL Server Management Studio(SSMS)をインストールします。SSMSは、Microsoftが提供するSQL Server用のクライアントツールです。以下のリンクからダウンロードしてください。
- [SQL Server Management Studio (SSMS)](https://docs.microsoft.com/en-us/sql/ssms/download-sql-server-management-studio-ssms)

2. SSMSを起動し、接続情報を入力します。以下の情報を入力して、「Connect」ボタンをクリックします。
- Server type: Database Engine
- Server name: localhost
- Authentication: SQL Server Authentication
- Login: sa
- Password: YourStrong!Passw0rd (Docker Composeで設定したパスワード)

3. 接続が成功すると、Object Explorerに接続先のサーバーが表示されます。ここで、新しいクエリウィンドウを開きます。

4. クエリウィンドウに、実行したいSQL文を入力します。例えば、以下のようなSQL文を実行してみましょう。

```sql
SELECT * FROM sys.databases;
```

5. SQL文を実行するには、「Execute」ボタンをクリックするか、F5キーを押します。実行結果が下部の「Results」ペインに表示されます。

以上の手順で、SQL Serverを構築してから実際にSQLを実行することができます。SSMSを使うことで、SQL文の入力や実行結果の確認が簡単に行えます。

まとめ
Dockerを使用することで、手軽にSQL Serverを構築することができます。今回は、SQLパズルを解くためにDockerでSQL Serverを構築しましたが、その他の用途でも活用できることでしょう。