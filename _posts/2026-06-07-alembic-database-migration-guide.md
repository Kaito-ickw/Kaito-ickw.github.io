---
layout: post
title: "Alembic でデータベーススキーマの変更を管理する"
subtitle: SQLAlchemy との関係、マイグレーションの仕組み、既存DBへの導入までやさしく解説
categories: 開発
tags: ["Alembic", "SQLAlchemy", "PostgreSQL", "データベース", "マイグレーション", "AIネイティブ開発"]
lang: ja
ref: alembic-database-migration-guide
image:
  path: /assets/images/posts/2026-06-07-alembic-database-migration-guide/eyecatch.png
  alt: 三つのデータ保管庫を一列の改修台車が同じ順序で変更していくミニチュア工房
---

AI ネイティブなログアプリの Phase 2 では、テーブル追加やカラム変更が増えてくる。

開発初期は Supabase の SQL Editor や `psql` で直接 DDL を実行しても進められる。しかし、環境や開発者が増えると、次の問題が起きやすい。

- 開発環境と本番環境でテーブル構造が違う
- 誰が、いつ、何のためにカラムを追加したのか分からない
- 新しい環境に同じスキーマを再現できない
- AI が生成した SQL をどこまで適用したのか追跡できない
- アプリケーションと DB のどちらを先に更新すべきか判断できない

そこで Phase 2 では、データベース変更をコードとして管理するために **Alembic** を導入する予定である。

ただ、「Alembic は何者なのか」「SQLAlchemy と何が違うのか」「DDL の正本にするとはどういう意味か」がまだ曖昧だったため、この記事で基礎から整理する。

---

## 結論を先に

Alembic は、Python の SQL ツールキットである SQLAlchemy と組み合わせて使う、**データベースマイグレーションツール**である。

データベースに対して実行する変更を、次のような Python ファイルとして Git で管理する。

```python
def upgrade() -> None:
    op.add_column(
        "events",
        sa.Column("trace_id", sa.String(length=64), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("events", "trace_id")
```

このファイルを使って、開発・テスト・ステージング・本番の各 DB に同じ変更を順番に適用する。

```bash
alembic upgrade head
```

一言で表すなら、Alembic の役割は次のとおりである。

> データベースを直接書き換えるのではなく、再現可能な変更手順をコードとして残し、すべての環境へ同じ順序で適用する。

Alembic はデータベースそのものではない。ORM でもバックアップツールでもない。**DB スキーマの変更履歴と適用状態を管理するツール**である。

---

## そもそも DDL とは

DDL は **Data Definition Language** の略で、テーブル・カラム・インデックスなど、データベースの構造を定義する SQL を指す。

代表的な DDL は次のとおり。

```sql
CREATE TABLE events (...);

ALTER TABLE events
ADD COLUMN trace_id VARCHAR(64);

CREATE INDEX ix_events_trace_id
ON events (trace_id);

DROP TABLE old_events;
```

一方、行データを追加・更新・削除する `INSERT`、`UPDATE`、`DELETE` は DML (Data Manipulation Language) と呼ばれる。

| 分類 | 主な命令 | 対象 |
| :--- | :--- | :--- |
| DDL | `CREATE`、`ALTER`、`DROP` | テーブルやカラムなどの構造 |
| DML | `INSERT`、`UPDATE`、`DELETE` | テーブル内のデータ |
| DQL | `SELECT` | データの検索 |

Alembic の中心的な役割は DDL の変更管理だが、必要に応じてデータ移行用の SQL や Python 処理も migration に含められる。

---

## マイグレーションとは

マイグレーションは、DB をある状態から次の状態へ移すための変更手順である。

たとえば、最初は次の `events` テーブルだけがあったとする。

```text
events
├── id
├── occurred_at
└── payload
```

Phase 2 で AI エージェントの実行単位を追跡するため、`trace_id` を追加する。

```text
events
├── id
├── occurred_at
├── trace_id       ← 追加
└── payload
```

SQL を手作業で実行するだけなら、その瞬間の DB は更新できる。しかし、別の環境で同じ変更を再現するには、実行した SQL・順序・前提条件を人間が覚えておかなければならない。

Alembic では、この変更を revision ファイルとして残す。

```text
<base>
  ↓
001_create_events
  ↓
002_add_trace_id
  ↓
003_add_trace_id_index
```

各ファイルが DB の変更を一段ずつ表すため、どの環境でも同じ履歴をたどれる。

---

## 「DDL の正本」にするとはどういうことか

「Alembic を DDL の正本にする」という表現は、少し分解して理解した方がよい。

Alembic を導入しても、SQLAlchemy のモデルや実際の DB が不要になるわけではない。それぞれ役割が異なる。

| 対象 | 役割 |
| :--- | :--- |
| SQLAlchemy モデル | アプリが期待する**現在のスキーマ**を表す |
| Alembic revision | 現在のスキーマへ至る**変更手順と履歴**を表す |
| 実際の DB | migration を適用した**実行時の状態** |

たとえば SQLAlchemy モデルは、現在の完成形を表現する。

```python
class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    trace_id: Mapped[str | None] = mapped_column(String(64), index=True)
```

しかし、このモデルだけを見ても次のことは分からない。

- `trace_id` は最初からあったのか
- 既存データをどう移行したのか
- 一時的に nullable にしてから必須化したのか
- 本番環境へどの順序で適用するのか

この時間軸を持つのが Alembic revision である。

したがって、Phase 2 での「DDL の正本」は、次の運用を意味する。

> DB 構造を変更するときは必ず Alembic revision を作成し、Git に保存された migration を通して各環境へ適用する。

本番 DB の管理画面で直接 DDL を実行したり、アプリ起動時に `Base.metadata.create_all()` で不足テーブルを作ったりすると、Alembic の履歴に残らない変更が生まれる。これを **スキーマドリフト** と呼ぶ。

厳密には、Alembic は「完成形を1ファイルで宣言する正本」ではない。**DB を再現するための正式な変更履歴**が正本になる、と考えると分かりやすい。

---

## Alembic と SQLAlchemy の違い

両者は密接に連携するが、担当範囲は別である。

| | SQLAlchemy | Alembic |
| :--- | :--- | :--- |
| 主な役割 | Python から DB を操作する | DB スキーマの変更履歴を管理する |
| ORM | ある | ない |
| クエリ実行 | する | migration 内で限定的に行う |
| モデル定義 | する | モデルを参照できる |
| スキーマ差分 | `MetaData` に現在形を持つ | DB と `MetaData` を比較できる |
| バージョン管理 | しない | revision と適用状態を管理する |

SQLAlchemy が「アプリケーションと DB をつなぐ道具」なら、Alembic は「DB の構造変更を安全に運ぶ道具」である。

Alembic は内部で SQLAlchemy を利用するため、Python コードで書いた操作を PostgreSQL など各 DB 向けの DDL に変換できる。

```python
op.create_index(
    "ix_events_trace_id",
    "events",
    ["trace_id"],
    unique=False,
)
```

PostgreSQL では、おおむね次の SQL として実行される。

```sql
CREATE INDEX ix_events_trace_id
ON events (trace_id);
```

---

## Alembic の構成ファイル

Alembic を初期化すると、migration を管理するためのディレクトリと設定ファイルが作られる。

```bash
uv add alembic
alembic init migrations
```

典型的な構成は次のとおり。

```text
project/
├── alembic.ini
├── pyproject.toml
├── migrations/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── 8a32_create_events.py
│       └── b51f_add_trace_id.py
└── src/
    └── models/
```

### `alembic.ini`

Alembic の基本設定を持つ。

- migration ディレクトリの場所
- DB 接続設定
- ログ設定
- revision ファイル名の形式

DB のパスワードを Git 管理する `alembic.ini` に直接書くのは避け、通常は `env.py` で環境変数から接続 URL を渡す。

### `migrations/env.py`

Alembic の実行方法を決める中心ファイル。

SQLAlchemy モデルから migration を自動生成する場合は、モデルの `MetaData` を `target_metadata` に設定する。

```python
from app.db.base import Base

target_metadata = Base.metadata
```

### `migrations/versions/`

revision ファイルを保存する場所。

このディレクトリのファイルが DB の変更履歴になるため、アプリケーションコードと一緒に Git へコミットする。

---

## revision ファイルの中身

revision ファイルには、識別子と変更処理が記録される。

```python
"""add trace id to events

Revision ID: b51f0c2a914e
Revises: 8a32fd69c102
"""

from alembic import op
import sqlalchemy as sa


revision = "b51f0c2a914e"
down_revision = "8a32fd69c102"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "events",
        sa.Column("trace_id", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "ix_events_trace_id",
        "events",
        ["trace_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_events_trace_id", table_name="events")
    op.drop_column("events", "trace_id")
```

重要な要素は次の4つ。

| 要素 | 意味 |
| :--- | :--- |
| `revision` | この変更を識別する一意な ID |
| `down_revision` | 一つ前の revision ID |
| `upgrade()` | 新しい状態へ進める処理 |
| `downgrade()` | 前の状態へ戻す処理 |

`down_revision` によって revision 同士がつながり、変更履歴が構成される。

---

## `alembic_version` テーブル

Alembic を DB に適用すると、通常は `alembic_version` という管理用テーブルが作られる。

```sql
SELECT * FROM alembic_version;
```

```text
 version_num
--------------
 b51f0c2a914e
```

この値は「この DB がどの revision まで適用済みか」を示す。

Alembic は次の2つを比較して、未適用の変更を判断する。

```text
Git にある revision 履歴
            +
DB の alembic_version
            ↓
次に実行すべき migration
```

`alembic_version` はテーブル定義そのものを保存する場所ではない。現在位置を示すポインタに近い。

---

## 基本コマンド

よく使うコマンドをまとめる。

| コマンド | 用途 |
| :--- | :--- |
| `alembic init migrations` | migration 環境を初期化する |
| `alembic revision -m "message"` | 空の revision を作る |
| `alembic revision --autogenerate -m "message"` | モデルと DB の差分から候補を作る |
| `alembic upgrade head` | 最新 revision まで適用する |
| `alembic downgrade -1` | 一つ前へ戻す |
| `alembic current` | DB の現在 revision を確認する |
| `alembic history` | revision 履歴を表示する |
| `alembic heads` | 最新 revision を確認する |
| `alembic check` | 未作成のスキーマ差分があるか確認する |
| `alembic stamp head` | DDL を実行せず、適用済み位置だけを記録する |

普段の開発で中心になるのは、次の3つである。

```bash
alembic revision --autogenerate -m "add trace id to events"
alembic upgrade head
alembic current
```

---

## autogenerate は何をしているのか

`--autogenerate` を付けると、Alembic は次の2つを比較する。

1. 接続先 DB の現在のスキーマ
2. SQLAlchemy モデルの `MetaData`

```text
現在の DB
    ↕ 差分比較
SQLAlchemy MetaData
    ↓
revision の候補を生成
```

たとえばモデルに `trace_id` を追加してから、次のコマンドを実行する。

```bash
alembic revision --autogenerate -m "add trace id to events"
```

Alembic はカラム追加を検出し、`op.add_column()` を含む revision を生成する。

ただし、公式ドキュメントでも autogenerate の出力は **candidate migrations**、つまり候補として扱われている。生成されたファイルは必ず人間が確認・修正する必要がある。

### 検出しやすい変更

- テーブルの追加・削除
- カラムの追加・削除
- nullable の変更
- 基本的なインデックス変更
- 名前付き UNIQUE 制約
- 基本的な外部キー変更
- 主なカラム型の変更

### 自動判断できない、または注意が必要な変更

- テーブル名の変更
- カラム名の変更
- 匿名の制約
- 複雑な型変更
- データの変換や補完
- PostgreSQL の extension
- view、function、trigger
- Row Level Security の policy
- DB 固有の高度なオブジェクト

たとえば `old_name` を `new_name` に変更しても、Alembic は「名前変更」と判断できず、次のような危険な差分を作ることがある。

```python
op.add_column("events", sa.Column("new_name", sa.Text()))
op.drop_column("events", "old_name")
```

このまま適用すると `old_name` のデータを失う。

正しくは、生成結果を次のように修正する。

```python
op.alter_column(
    "events",
    "old_name",
    new_column_name="new_name",
)
```

> `--autogenerate` は migration の自動実行ではない。差分を推測して、レビュー対象の Python ファイルを作る機能である。

---

## 制約名を決めておく

PRIMARY KEY、FOREIGN KEY、UNIQUE、CHECK などの制約は、名前がないと DB が自動命名する場合がある。

環境ごとに名前が異なると、後の migration で制約を削除しにくい。SQLAlchemy の `MetaData.naming_convention` を使って、最初から命名規則を統一しておくとよい。

```python
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase


NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
```

この規則は Alembic の autogenerate とも連携する。

Phase 2 の開始時に命名規則を決めておく方が、テーブル数が増えてから既存制約を改名するより負担が小さい。

---

## PostgreSQL・Supabase 固有の DDL はどうするか

ログアプリでは、通常のテーブル定義以外にも PostgreSQL 固有機能を使う可能性がある。

- `pgvector` などの extension
- Row Level Security
- policy
- trigger
- function
- view
- 部分インデックス
- GIN インデックス

autogenerate が扱えない DDL は、revision を手動で作成して `op.execute()` などで明示する。

たとえば Supabase の `events` テーブルへ RLS policy を追加する場合は、次のように履歴へ残せる。

```python
from alembic import op


def upgrade() -> None:
    op.execute("ALTER TABLE events ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY events_select_own
        ON events
        FOR SELECT
        USING (user_id = auth.uid())
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY events_select_own ON events")
    op.execute("ALTER TABLE events DISABLE ROW LEVEL SECURITY")
```

重要なのは、Supabase の SQL Editor で実行するか Alembic で実行するかではなく、**正式な DB 変更を一つの経路へ統一すること**である。

Alembic を正本にするなら、SQL Editor は調査や一時的な検証に限定し、正式な DDL は revision に書いて適用する。

---

## 既存 DB に Alembic を導入する方法

Phase 2 から導入する場合、すでに開発 DB や Supabase 上にテーブルが存在している。

ここで、既存 DB に対していきなり初期 migration を実行すると、存在済みテーブルの `CREATE TABLE` が衝突する。

必要なのは **baseline**、つまり「Alembic 管理を開始する基準点」を作ることだ。

### 基本手順

1. 現在の DB と SQLAlchemy モデルを一致させる
2. 現在の全スキーマを作れる初期 revision を用意する
3. 空の一時 DB で `alembic upgrade head` を実行する
4. 作成されたスキーマが既存 DB と一致することを確認する
5. 既存 DB には DDL を実行せず `alembic stamp head` を実行する
6. 以後の変更はすべて新しい revision として追加する

```bash
# 空の検証用 DB では実際に初期スキーマを作る
alembic upgrade head

# 既存 DB では「ここまで適用済み」と記録するだけ
alembic stamp head
```

`stamp` は migration を実行しない。`alembic_version` の位置だけを更新する。

そのため、既存 DB と baseline が本当に同じ構造であることを確認せずに `stamp head` すると、Alembic は一致していると思っているのに実際には違う、という危険な状態になる。

また、既存 DB とモデルが一致した状態で `--autogenerate` を実行すると、差分がないため初期 revision は空になる。初期 revision を自動生成するなら、**空の DB とモデルを比較する**必要がある。

---

## Phase 2 での標準ワークフロー

テーブル変更を行う Pull Request は、次の流れに統一すると分かりやすい。

### 1. 手元の DB を最新化する

```bash
alembic upgrade head
```

古い DB を基準に revision を作ると、不要な差分や競合が生まれやすい。

### 2. SQLAlchemy モデルを変更する

```python
trace_id: Mapped[str | None] = mapped_column(String(64), index=True)
```

### 3. revision 候補を生成する

```bash
alembic revision --autogenerate -m "add trace id to events"
```

### 4. revision をレビューする

最低限、次を確認する。

- 意図しない `drop_table` や `drop_column` がないか
- カラム名変更が add + drop になっていないか
- nullable、default、型が正しいか
- index と constraint の名前が正しいか
- `downgrade()` の順序が正しいか
- 既存データがある状態で成功するか
- 長時間のロックやテーブル全体の書き換えが起きないか

### 5. migration を適用してテストする

```bash
alembic upgrade head
pytest
```

空の一時 DB でも先頭から適用できることを確認する。

```bash
alembic upgrade head
```

### 6. モデルと revision を同じ PR に含める

モデルだけ、または revision だけを先にマージすると、アプリと DB の期待がずれる。

### 7. デプロイ時に一度だけ適用する

```bash
alembic upgrade head
```

複数の Web コンテナが同時に migration を実行する構成は避ける。デプロイジョブなど、実行主体を一つに決める。

---

## CI で確認したいこと

AI や人間がモデルだけを変更し、revision を作り忘れる可能性がある。Alembic にはその差分を検出する `check` コマンドがある。

```bash
alembic check
```

`alembic revision --autogenerate` と同じ比較処理を行うが、revision ファイルは生成しない。未反映のスキーマ差分があれば CI を失敗させられる。

Phase 2 の最小 CI は次の構成が現実的である。

```bash
# 空の PostgreSQL に全 migration を適用
alembic upgrade head

# モデルと適用後 DB に差分がないことを確認
alembic check

# アプリケーションの振る舞いを確認
pytest
```

さらに `alembic heads` の結果が一つだけであることも確認すると、複数ブランチで同時に作られた revision の競合を早く検出できる。

---

## migration の競合と複数 head

2人または複数の AI エージェントが、同じ親 revision から別々の revision を作ることがある。

```text
             ┌─ 002_add_trace_id
001_events ──┤
             └─ 003_add_agent_name
```

この状態では最新地点が2つあり、`alembic upgrade head` の行き先が一意に決まらない。

```bash
alembic heads
```

通常は merge revision を作って、履歴を一つにまとめる。

```bash
alembic merge heads -m "merge migration heads"
```

```text
             ┌─ 002_add_trace_id ──┐
001_events ──┤                     ├─ 004_merge_heads
             └─ 003_add_agent_name ┘
```

既に共有された revision の `down_revision` を書き換えて直線化すると、適用済み環境の履歴と食い違う可能性がある。公開・共有済みの revision は原則として変更せず、merge revision で解決する方が安全である。

---

## 本番変更は expand / migrate / contract で考える

開発 DB では一度に成功する変更でも、本番では旧バージョンと新バージョンのアプリが一時的に同時稼働する。

たとえば既存カラムをいきなり削除すると、古いコンテナがそのカラムを参照してエラーになる。

大きな変更は3段階に分ける。

### 1. Expand

新しい構造を追加し、古いアプリでも動く状態を保つ。

```text
nullable な新カラムを追加
新テーブルを追加
新旧どちらでも読めるようにする
```

### 2. Migrate

既存データを移し、アプリを新しい構造へ切り替える。

```text
バックフィルを実行
新旧カラムへ二重書き
読み取り先を新カラムへ変更
```

### 3. Contract

古いコードが使われなくなってから、不要な構造を削除する。

```text
NOT NULL 制約を追加
旧カラムを削除
一時的な互換コードを削除
```

この分割により、スキーマ変更とアプリのデプロイ順序に余裕を持たせられる。

---

## データ migration は分けて考える

カラム追加のような schema migration と、何百万行もの既存データを書き換える data migration は性質が違う。

小規模なデータ補正なら revision に含められる。

```python
def upgrade() -> None:
    op.add_column(
        "events",
        sa.Column("status", sa.String(length=20), nullable=True),
    )
    op.execute("UPDATE events SET status = 'completed' WHERE status IS NULL")
    op.alter_column("events", "status", nullable=False)
```

しかし、大量データの更新を migration のトランザクション内で行うと、長時間ロックやタイムアウトが起きる可能性がある。

大規模なバックフィルは、次のように分離した方がよい。

1. revision で nullable なカラムを追加する
2. 専用ジョブで少量ずつバックフィルする
3. 未移行データがないことを確認する
4. 別 revision で `NOT NULL` を追加する

Alembic があるから、すべてのデータ処理を Alembic の中へ入れるべき、というわけではない。

---

## downgrade を過信しない

`downgrade()` があると、いつでも安全に元へ戻せるように見える。

しかし、次の変更は完全には元に戻せない。

- カラム削除
- テーブル削除
- データ型変換による情報欠落
- データの集約
- 外部システムと連動した更新

```python
def downgrade() -> None:
    op.add_column("events", sa.Column("deleted_value", sa.Text()))
```

カラム自体は再作成できても、削除前の値は戻らない。

本番障害では、古い migration へ戻すより、問題を修正する新しい revision を前向きに追加する **roll forward** の方が安全な場合も多い。

`downgrade()` は検証環境で役立つが、バックアップの代わりにはならない。

---

## Alembic が担当しないこと

Alembic を導入しても、データベース運用のすべてが解決するわけではない。

| 対象 | Alembic の担当 |
| :--- | :--- |
| DB スキーマの変更履歴 | 担当する |
| migration の適用順序 | 担当する |
| DB バックアップ | 担当しない |
| データ損失からの復旧 | 担当しない |
| SQL の性能保証 | 担当しない |
| migration の安全性レビュー | 自動では保証しない |
| アプリとの互換性 | テストとデプロイ設計が必要 |
| シークレット管理 | 担当しない |

特にバックアップと migration は別物である。

Alembic は「何を変更したか」を再現する。バックアップは「その時点でどんなデータが入っていたか」を復元する。

---

## AI ネイティブ開発で Alembic が重要な理由

AI エージェントは、SQLAlchemy モデルや SQL を高速に生成できる。一方で、生成量が増えるほど DB 変更の統制が重要になる。

### 1. AI の変更をレビュー可能な差分にする

AI が DB へ直接 SQL を実行すると、変更の意図と結果が会話ログに埋もれる。

revision ファイルとして出力させれば、通常のコードと同じように Git diff で確認できる。

### 2. 環境ごとの再現性を持たせる

どの AI や開発者が変更しても、適用経路を `alembic upgrade head` に統一できる。

### 3. 危険な変更を CI で止める

モデルだけが変更された状態は `alembic check` で検出できる。空 DB への全 migration 適用も自動テストできる。

### 4. AI に任せてはいけない判断を明確にする

AI が autogenerate の結果を説明・修正することはできる。しかし、次の判断には本番データと運用条件の理解が必要である。

- この `DROP COLUMN` は本当に不要か
- 既存行に NULL がないか
- インデックス作成で書き込みが止まらないか
- RLS policy が意図せずデータを公開しないか
- 旧アプリとの互換性が保たれるか

Alembic は AI に DB 変更を自由に任せるための道具ではない。**AI が作った変更を、レビュー・テスト・再実行できる形へ固定するための基盤**である。

---

## Phase 2 で決めておきたい運用ルール

今回のログアプリでは、最初から次のルールを置くと管理しやすい。

1. DB スキーマ変更は必ず Alembic revision にする
2. SQLAlchemy モデルと revision を同じ PR で変更する
3. 本番や Supabase の管理画面で正式な DDL を直接実行しない
4. アプリ起動時に `Base.metadata.create_all()` を実行しない
5. autogenerate の結果をそのまま信用せず、必ずレビューする
6. 適用済み・共有済み revision は原則として書き換えない
7. `alembic heads` は通常一つに保つ
8. CI で空 DB への `upgrade head` と `alembic check` を実行する
9. migration はデプロイ処理の中で一度だけ実行する
10. 大量データのバックフィルは schema migration と分離する

これらを守ることで、Alembic のファイルと実 DB の履歴が一致しやすくなる。

---

## 導入時の最小構成

Phase 2 の最初から複雑な仕組みを作る必要はない。

### 1. Alembic を追加する

```bash
uv add alembic
```

### 2. migration 環境を作る

```bash
alembic init migrations
```

### 3. `env.py` にモデルの MetaData を設定する

```python
from app.db.base import Base

target_metadata = Base.metadata
```

### 4. 既存 DB の baseline を作る

空 DB への `upgrade head` と既存 DB との差分を確認し、既存 DB を `stamp head` する。

### 5. CI に最低限の検証を追加する

```bash
alembic upgrade head
alembic check
pytest
```

### 6. 以後の変更経路を統一する

```bash
# モデル変更後
alembic revision --autogenerate -m "describe schema change"

# 生成ファイルをレビュー

# 開発 DB へ適用
alembic upgrade head
```

この構成だけでも、手作業の DDL と環境差分を大きく減らせる。

---

## まとめ

| ポイント | 内容 |
| :--- | :--- |
| Alembic の正体 | SQLAlchemy と連携する DB migration ツール |
| 主な役割 | DDL の変更手順・順序・適用状態を管理する |
| SQLAlchemy との違い | モデルは現在形、Alembic はそこへ至る変更履歴 |
| 基本単位 | `upgrade()` と `downgrade()` を持つ revision ファイル |
| 現在位置 | DB の `alembic_version` テーブルで追跡する |
| 自動生成 | モデルと DB の差分から候補を作るが、レビューは必須 |
| 既存 DB への導入 | baseline を作り、検証後に `stamp` する |
| PostgreSQL 固有機能 | 手書き revision と `op.execute()` で管理する |
| AI 開発での価値 | AI が生成した DB 変更をレビュー可能・再現可能にする |

Alembic の価値は、単に `ALTER TABLE` を Python で書けることではない。

**データベース変更を会話・手作業・管理画面から切り離し、アプリケーションコードと同じようにレビュー、テスト、バージョン管理できること**にある。

Phase 1 の個人開発では、直接 SQL を実行する方が速い場面もある。しかし、Phase 2 で環境・機能・開発主体が増えるなら、DB の変更履歴を正式な資産として管理する必要がある。

Alembic を DDL の正本にするとは、ツールを一つ追加することではない。**DB を変更する正式な経路を一つに決めること**である。

---

## 参考

- [Alembic 公式ドキュメント](https://alembic.sqlalchemy.org/en/latest/)
- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [Auto Generating Migrations](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)
- [Alembic Command Reference](https://alembic.sqlalchemy.org/en/latest/api/commands.html)
- [The Importance of Naming Constraints](https://alembic.sqlalchemy.org/en/latest/naming.html)
- [Working with Branches](https://alembic.sqlalchemy.org/en/latest/branches.html)
- [Alembic Operation Reference](https://alembic.sqlalchemy.org/en/latest/ops.html)
- [SQLAlchemy ── Defining Constraints and Indexes](https://docs.sqlalchemy.org/en/20/core/constraints.html)
