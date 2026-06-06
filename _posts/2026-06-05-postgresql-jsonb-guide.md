---
layout: post
title: "PostgreSQL JSONB 完全ガイド ── 柔軟なスキーマ設計と高速クエリの両立"
subtitle: JSON vs JSONB の違いから GIN インデックス・演算子まで実践的に解説
categories: 開発
tags: ["PostgreSQL", "JSONB", "データベース", "SQL"]
---

「スキーマが固まっていない段階でもデータを保存したい」「フィールドが動的に増減する構造を扱いたい」── こういった要件に直面したとき、PostgreSQL の **JSONB** 型が選択肢に上がることが多い。

この記事では JSONB の基本から、実用的なクエリ・インデックス設計・パフォーマンス特性まで体系的に整理する。

---

## JSON と JSONB ── 何が違うのか

PostgreSQL には JSON を格納する型が 2 種類ある。

| | `json` | `jsonb` |
| :--- | :--- | :--- |
| **内部表現** | テキストそのまま保存 | バイナリ形式に変換して保存 |
| **書き込みコスト** | 低い (変換なし) | やや高い (バイナリ変換あり) |
| **読み取りコスト** | 高い (毎回パース) | 低い (バイナリ直読み) |
| **インデックス** | 部分的なサポート | GIN インデックスが使える |
| **キーの重複** | 保持する | 最後の値が残る |
| **キーの順序** | 保持する | 保証されない |
| **演算子** | 基本的なもののみ | 豊富 (`@>`, `?`, `?|`, `?&` 等) |

実用上、**書き込みより読み取りが多く、検索を行うなら JSONB 一択**。`json` 型を選ぶのはキーの順序や重複を完全に保持しなければならない特殊なケースに限られる。

---

## テーブル設計の基本

```sql
CREATE TABLE events (
    id          BIGSERIAL PRIMARY KEY,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source      TEXT        NOT NULL,
    payload     JSONB       NOT NULL
);
```

`payload` カラムに何でも詰め込める設計。スキーマが安定したフィールド (`occurred_at`, `source`) はリレーショナルカラムとして持ち、可変部分だけを JSONB に任せるのが典型的なパターン。

---

## 基本的な読み書き

### 書き込み

```sql
INSERT INTO events (source, payload)
VALUES (
    'api',
    '{"user_id": 42, "action": "login", "metadata": {"ip": "192.168.1.1", "ua": "Mozilla/5.0"}}'
);
```

### フィールド取得

```sql
-- テキストとして取得
SELECT payload->>'user_id'   AS user_id,
       payload->>'action'    AS action
FROM   events;

-- JSON として取得 (ネストしたオブジェクトをそのまま取り出す)
SELECT payload->'metadata' AS meta
FROM   events;

-- ネストを一気に辿る
SELECT payload #>> '{metadata, ip}' AS ip_address
FROM   events;
```

演算子の使い分け：

| 演算子 | 返り値 | 用途 |
| :--- | :--- | :--- |
| `->` | `jsonb` | ネストした JSON を取り出す |
| `->>` | `text` | 末端の値をテキストで取り出す |
| `#>` | `jsonb` | パス配列で辿る |
| `#>>` | `text` | パス配列で辿り、テキストで返す |

---

## 検索クエリ

### 完全一致・包含検索

```sql
-- payload が指定オブジェクトを "含む" かどうか (@> 演算子)
SELECT * FROM events
WHERE  payload @> '{"action": "login"}';

-- キーの存在チェック
SELECT * FROM events
WHERE  payload ? 'user_id';

-- いずれかのキーが存在
SELECT * FROM events
WHERE  payload ?| ARRAY['user_id', 'session_id'];

-- すべてのキーが存在
SELECT * FROM events
WHERE  payload ?& ARRAY['action', 'metadata'];
```

### 型キャストを伴う比較

JSONB のフィールドを数値・日付として比較するには明示的なキャストが必要。

```sql
-- 数値比較
SELECT * FROM events
WHERE  (payload->>'user_id')::INTEGER > 100;

-- 日付比較
SELECT * FROM events
WHERE  (payload->>'created_at')::TIMESTAMPTZ > NOW() - INTERVAL '1 hour';
```

### 配列フィールドの検索

```sql
-- tags 配列が "error" を含む行
SELECT * FROM events
WHERE  payload->'tags' @> '["error"]';
```

---

## GIN インデックス ── JSONB 検索の要

JSONB の検索を高速化するのが **GIN (Generalized Inverted Index)** インデックス。

### デフォルト GIN

```sql
CREATE INDEX idx_events_payload ON events USING GIN (payload);
```

`@>`, `?`, `?|`, `?&` の各演算子が対象。ほとんどのユースケースはこれで事足りる。

### jsonb_path_ops

```sql
CREATE INDEX idx_events_payload_path ON events
USING GIN (payload jsonb_path_ops);
```

`@>` のみに特化したオペレータークラス。インデックスサイズが小さくなりパフォーマンスが向上するケースが多い。`?` 系の演算子は使えなくなるので注意。

### 特定フィールドへの B-Tree インデックス

```sql
-- user_id だけ頻繁に検索する場合
CREATE INDEX idx_events_user_id
ON events ((payload->>'user_id'));

-- 数値として検索するなら型キャストも含める
CREATE INDEX idx_events_user_id_int
ON events (((payload->>'user_id')::INTEGER));
```

特定フィールドへのポイントクエリが多い場合、GIN より B-Tree の方が効率が良いことがある。

---

## jsonb_path_query ── JSONPath 検索

PostgreSQL 12 以降、**JSONPath** 構文でより柔軟な検索ができる。

```sql
-- action が "error" かつ severity が 3 以上のイベントを抽出
SELECT *
FROM   events
WHERE  payload @? '$.action ? (@ == "error") && $.severity ? (@ >= 3)';

-- jsonb_path_query で値を取り出す
SELECT jsonb_path_query(payload, '$.metadata.ip')
FROM   events
WHERE  source = 'api';
```

---

## 集計・集計関数

### フィールドでのグループ集計

```sql
SELECT payload->>'action'    AS action,
       COUNT(*)              AS cnt
FROM   events
GROUP  BY payload->>'action'
ORDER  BY cnt DESC;
```

### jsonb_agg / jsonb_object_agg

```sql
-- source ごとに payload を配列として集約
SELECT source,
       jsonb_agg(payload ORDER BY occurred_at) AS payloads
FROM   events
GROUP  BY source;
```

---

## スキーマの進化への対応

JSONB の強みのひとつは**スキーマを後から変更できる**点にある。

### フィールドの追加・更新

```sql
-- 既存行に新しいフィールドを追加
UPDATE events
SET    payload = payload || '{"version": 2}'
WHERE  source = 'api';

-- ネストしたフィールドを更新
UPDATE events
SET    payload = jsonb_set(payload, '{metadata, processed}', 'true')
WHERE  id = 42;
```

### フィールドの削除

```sql
-- トップレベルのキーを削除
UPDATE events
SET    payload = payload - 'deprecated_field';

-- ネストしたキーを削除
UPDATE events
SET    payload = payload #- '{metadata, tmp}';
```

---

## パフォーマンス設計のポイント

### JSONB vs リレーショナルカラム

JSONB はあくまでも「柔軟性のトレードオフ」として使うものであり、**クエリが頻繁で固定的なフィールドはリレーショナルカラムに昇格させる**のが原則。

| 状況 | 推奨 |
| :--- | :--- |
| 検索・結合頻度が高い | リレーショナルカラム |
| スキーマが流動的・フィールドが多様 | JSONB |
| 読み取りより書き込みが圧倒的に多い | JSONB (ただし GIN は慎重に) |
| 全文検索や類似検索が必要 | 別カラム + tsvector / pgvector |

### GIN インデックスのコスト

GIN インデックスは **書き込みコストが高い**。大量の INSERT が走るユースケースでは `fastupdate = off` を検討するか、インデックスを絞り込む。

```sql
-- fastupdate を無効にして書き込み遅延を減らす
CREATE INDEX idx_events_payload ON events
USING GIN (payload) WITH (fastupdate = off);
```

### EXPLAIN ANALYZE で確認

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM events
WHERE  payload @> '{"action": "error"}';
```

`Bitmap Index Scan on idx_events_payload` が出ていれば GIN インデックスが使われている。`Seq Scan` なら統計情報の更新 (`ANALYZE`) や条件の見直しが必要。

---

## 生成カラムとの組み合わせ (PostgreSQL 12+)

繰り返しキャストするフィールドは **生成カラム (generated column)** にしておくと便利。

```sql
ALTER TABLE events
ADD COLUMN user_id INTEGER
    GENERATED ALWAYS AS ((payload->>'user_id')::INTEGER) STORED;

CREATE INDEX idx_events_uid ON events (user_id);
```

JSONB の柔軟性を保ちつつ、特定フィールドへの高速アクセスを両立できる。

---

## まとめ

| トピック | ポイント |
| :--- | :--- |
| **json vs jsonb** | 検索・インデックスが必要なら JSONB 一択 |
| **演算子** | `@>` (包含)・`?` (キー存在) が主役 |
| **インデックス** | GIN が基本。ポイントクエリ多用なら B-Tree も検討 |
| **スキーマ進化** | `||` で追記・`jsonb_set` で更新・`-` で削除 |
| **固定フィールド** | 頻繁に検索するものはリレーショナルカラムに昇格 |
| **生成カラム** | JSONB と B-Tree の良いとこ取りができる |

JSONB は「何でも入る箱」として使いすぎると後からクエリの最適化が困難になる。**固定部分はリレーショナル、可変部分は JSONB** という役割分担を意識することが、長期的に保守しやすい設計につながる。

---

## 参考

- [PostgreSQL 公式ドキュメント ── JSON Functions and Operators](https://www.postgresql.org/docs/current/functions-json.html)
- [PostgreSQL 公式ドキュメント ── jsonb Indexing](https://www.postgresql.org/docs/current/datatype-json.html#JSON-INDEXING)
- [Use The Index, Luke ── Indexing JSON](https://use-the-index-luke.com/)
