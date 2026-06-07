---
layout: post
title: "OpenAPI とは何か ── API 仕様を「人間にも機械にも読めるドキュメント」にする仕組み"
subtitle: Swagger との関係から YAML の書き方、コード生成・Postman 連携まで一気に理解する
categories: 開発
tags: ["OpenAPI", "Swagger", "API", "REST", "バックエンド", "ドキュメント"]
lang: ja
ref: openapi-guide
---

API を開発していると、こんな場面に必ず出くわす。

- フロントエンドとバックエンドで「パラメータ名が違う」「レスポンスの形が変わった」が頻発する
- Postman のコレクションを手で更新し続けるのが辛い
- API の仕様をドキュメントに書いたが、コードと乖離してきた
- 他チームや外部パートナーに API を公開したい

これらは根本的に同じ問題だ。**API の仕様がどこか一か所にまとまっていない**。

OpenAPI は、その「一か所」をつくるための仕様である。

---

## 結論を先に

OpenAPI とは、**REST API の仕様を YAML または JSON で記述するためのフォーマット標準**である。

```yaml
# openapi.yaml の最小例
openapi: "3.1.0"
info:
  title: My API
  version: "1.0.0"
paths:
  /users/{id}:
    get:
      summary: ユーザーを1件取得する
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      responses:
        "200":
          description: 成功
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/User"
components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: integer
        name:
          type: string
        email:
          type: string
```

この YAML ファイルひとつあれば、次のことが自動でできる。

- **Swagger UI** でブラウザから API を試せるドキュメントを生成
- **TypeScript / Python / Go** など各言語のクライアントコードを生成
- **Postman** や **Insomnia** に読み込んでそのまま動作確認
- **バリデーション** でリクエスト・レスポンスがスキーマ通りか自動チェック

---

## OpenAPI と Swagger の関係

よく混同される。整理すると次のとおりだ。

| 名前 | 正体 |
| :--- | :--- |
| **Swagger** | SmartBear 社が開発した、API 仕様記述フォーマット（旧称） |
| **OpenAPI** | Swagger 2.0 を Linux Foundation に寄贈して改名した標準仕様（現在の正式名） |
| **Swagger UI / Editor** | OpenAPI ファイルを可視化・編集するツール群（現在も Swagger の名前を使用） |

つまり「Swagger 仕様」と「OpenAPI 仕様」はほぼ同義だが、正式名は **OpenAPI**。ツールとしての "Swagger" は今も存在する。

現行のバージョンは **OpenAPI 3.1**（2021年リリース）。古いコードベースには 2.0 が残っていることもある。

---

## なぜ OpenAPI が必要なのか

### 問題: ドキュメントとコードが別々に生きている

「API ドキュメントは Confluence に書いてあるが、半年前から更新されていない」
「フロントエンドが叩いてみたらレスポンスのキー名が違った」

これは珍しくない。コードを変えるたびにドキュメントも手で直さないといけない構造になっているからだ。

### 解決: 仕様ファイルをコードと同じリポジトリで管理する

OpenAPI ファイルをリポジトリに入れてバージョン管理することで、次のことが変わる。

- コードの変更と仕様の変更が同じ PR に入る
- CI で仕様とコードが一致しているか自動チェックできる
- 仕様ファイルから直接クライアントコードを生成するため、手書きの型定義が不要になる

---

## OpenAPI ファイルの構造を理解する

OpenAPI ファイルは大きく 4 つのセクションで構成される。

### 1. メタ情報（`info`）

```yaml
openapi: "3.1.0"
info:
  title: Logging API
  description: AIネイティブなログ管理サービスの API
  version: "2.0.0"
  contact:
    email: support@example.com
```

### 2. エンドポイント定義（`paths`）

```yaml
paths:
  /logs:
    get:
      operationId: listLogs
      summary: ログ一覧を取得
      tags: [logs]
      parameters:
        - name: limit
          in: query
          schema:
            type: integer
            default: 20
            maximum: 100
      responses:
        "200":
          description: 成功
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/Log"
    post:
      operationId: createLog
      summary: ログを記録
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/CreateLogInput"
      responses:
        "201":
          description: 作成完了
```

### 3. スキーマ定義（`components/schemas`）

型の定義はここに集約し、`$ref` で参照する。重複を避けるためのしくみだ。

```yaml
components:
  schemas:
    Log:
      type: object
      required: [id, message, level, createdAt]
      properties:
        id:
          type: string
          format: uuid
        message:
          type: string
        level:
          type: string
          enum: [debug, info, warn, error]
        createdAt:
          type: string
          format: date-time

    CreateLogInput:
      type: object
      required: [message, level]
      properties:
        message:
          type: string
        level:
          type: string
          enum: [debug, info, warn, error]
```

### 4. 認証定義（`components/securitySchemes`）

```yaml
components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

security:
  - BearerAuth: []
```

---

## 実際にどう使うか

### パターン1: Design-First（仕様を先に書く）

1. `openapi.yaml` を先に書く
2. そこからクライアント SDK・サーバースタブを生成する
3. サーバー実装を進める

チーム開発で「フロントとバックが同時に動く」ときに有効。バックエンドが完成する前にフロントのコードを書き始められる。

### パターン2: Code-First（コードから生成する）

1. バックエンドのコードに OpenAPI のアノテーションを書く
2. ビルド時に `openapi.yaml` を自動生成する

FastAPI（Python）は最初からこれができる。

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class User(BaseModel):
    id: int
    name: str
    email: str

@app.get("/users/{id}", response_model=User)
def get_user(id: int):
    return {"id": id, "name": "Kaito", "email": "kaito@example.com"}
```

FastAPI でサーバーを起動すると `/docs` に Swagger UI が自動で生成される。`openapi.json` も `/openapi.json` で取得できる。

---

## よく使うツール

| ツール | 用途 |
| :--- | :--- |
| **Swagger Editor** | ブラウザ上で YAML を編集しながらプレビュー |
| **Swagger UI** | OpenAPI ファイルから HTML ドキュメントを生成 |
| **Redoc** | Swagger UI より見やすいドキュメント生成ツール |
| **openapi-generator** | 50 以上の言語向けにクライアント・サーバーコードを生成 |
| **Prism** | OpenAPI ファイルからモックサーバーを即座に立ち上げる |
| **Stoplight Studio** | GUI で OpenAPI を設計できるエディタ |

### openapi-generator でクライアント生成

```bash
# TypeScript の axios クライアントを生成
npx @openapitools/openapi-generator-cli generate \
  -i openapi.yaml \
  -g typescript-axios \
  -o src/generated/api
```

生成されたコードには型情報も含まれるため、フロントエンドで型エラーが起きにくくなる。

---

## CI での活用

OpenAPI の仕様が正しく書かれているか、GitHub Actions で自動チェックできる。

```yaml
# .github/workflows/openapi-lint.yml
name: OpenAPI Lint
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Validate OpenAPI spec
        uses: openapi-generators/openapitools-generator-action@v1
        with:
          generator: openapi
          openapi-file: openapi.yaml
          command-args: validate
```

また **Spectral**（Stoplight 製）を使えば、チーム独自のルール（命名規則・必須フィールドなど）を lint できる。

---

## まとめ

OpenAPI は、API の仕様を YAML で一元管理するための標準フォーマットだ。

- **ドキュメントが自動生成される** → Confluence に手書きしなくていい
- **クライアントコードが自動生成される** → 型の不一致がなくなる
- **モックサーバーが立てられる** → バックエンド完成前にフロントを開発できる
- **CI でバリデーションできる** → 仕様の崩れを早期に検知できる

特に **FastAPI** を使うなら、コードを書くだけで OpenAPI ドキュメントが自動生成されるため、導入コストがほぼゼロだ。まず FastAPI でサーバーを立ち上げて `/docs` を確認してみるのが、OpenAPI を体感する最短ルートだと思う。
