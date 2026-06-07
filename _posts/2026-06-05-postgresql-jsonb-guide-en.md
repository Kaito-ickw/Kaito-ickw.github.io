---
layout: post
title: "The Complete Guide to PostgreSQL JSONB — Flexible Schemas and Fast Queries"
subtitle: A practical guide to JSON vs JSONB, GIN indexes, operators, and more
categories: Development
tags: ["PostgreSQL", "JSONB", "Database", "SQL"]
lang: en
ref: postgresql-jsonb-guide
---

When requirements include "store data before the schema is finalized" or "handle structures whose fields change dynamically," PostgreSQL's **JSONB** type is often a strong option.

This article provides a systematic guide to JSONB, from the fundamentals to practical queries, index design, and performance characteristics.

---

## JSON vs JSONB — What Is the Difference?

PostgreSQL provides two types for storing JSON.

| | `json` | `jsonb` |
| :--- | :--- | :--- |
| **Internal representation** | Stored as the original text | Converted to and stored in a binary format |
| **Write cost** | Low (no conversion) | Slightly higher (binary conversion required) |
| **Read cost** | High (parsed every time) | Low (read directly from binary representation) |
| **Indexes** | Limited support | Supports GIN indexes |
| **Duplicate keys** | Preserved | Only the last value is retained |
| **Key order** | Preserved | Not guaranteed |
| **Operators** | Basic operators only | Rich set (`@>`, `?`, `?|`, `?&`, etc.) |

In practice, **JSONB is the clear choice when reads outnumber writes and the data must be searchable**. The `json` type is mainly useful in unusual cases where key order or duplicate keys must be preserved exactly.

---

## Basic Table Design

```sql
CREATE TABLE events (
    id          BIGSERIAL PRIMARY KEY,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source      TEXT        NOT NULL,
    payload     JSONB       NOT NULL
);
```

This design allows any structure to be stored in the `payload` column. A common pattern is to keep stable fields such as `occurred_at` and `source` as relational columns and use JSONB only for the variable portion.

---

## Basic Reads and Writes

### Writing Data

```sql
INSERT INTO events (source, payload)
VALUES (
    'api',
    '{"user_id": 42, "action": "login", "metadata": {"ip": "192.168.1.1", "ua": "Mozilla/5.0"}}'
);
```

### Retrieving Fields

```sql
-- Retrieve values as text
SELECT payload->>'user_id'   AS user_id,
       payload->>'action'    AS action
FROM   events;

-- Retrieve a nested object as JSON
SELECT payload->'metadata' AS meta
FROM   events;

-- Traverse a nested path directly
SELECT payload #>> '{metadata, ip}' AS ip_address
FROM   events;
```

How to choose an operator:

| Operator | Return type | Use |
| :--- | :--- | :--- |
| `->` | `jsonb` | Retrieve nested JSON |
| `->>` | `text` | Retrieve a leaf value as text |
| `#>` | `jsonb` | Traverse a path array |
| `#>>` | `text` | Traverse a path array and return text |

---

## Search Queries

### Exact and Containment Searches

```sql
-- Check whether payload contains the specified object (@> operator)
SELECT * FROM events
WHERE  payload @> '{"action": "login"}';

-- Check whether a key exists
SELECT * FROM events
WHERE  payload ? 'user_id';

-- Check whether any of the keys exist
SELECT * FROM events
WHERE  payload ?| ARRAY['user_id', 'session_id'];

-- Check whether all keys exist
SELECT * FROM events
WHERE  payload ?& ARRAY['action', 'metadata'];
```

### Comparisons with Type Casts

JSONB fields must be cast explicitly when comparing them as numbers or dates.

```sql
-- Numeric comparison
SELECT * FROM events
WHERE  (payload->>'user_id')::INTEGER > 100;

-- Date comparison
SELECT * FROM events
WHERE  (payload->>'created_at')::TIMESTAMPTZ > NOW() - INTERVAL '1 hour';
```

### Searching Array Fields

```sql
-- Rows whose tags array contains "error"
SELECT * FROM events
WHERE  payload->'tags' @> '["error"]';
```

---

## GIN Indexes — The Key to Fast JSONB Searches

JSONB searches can be accelerated with a **GIN (Generalized Inverted Index)** index.

### Default GIN Index

```sql
CREATE INDEX idx_events_payload ON events USING GIN (payload);
```

This supports the `@>`, `?`, `?|`, and `?&` operators. It is sufficient for most use cases.

### jsonb_path_ops

```sql
CREATE INDEX idx_events_payload_path ON events
USING GIN (payload jsonb_path_ops);
```

This operator class is specialized for `@>`. It often produces a smaller index and better performance, but does not support the `?` family of operators.

### B-Tree Indexes on Specific Fields

```sql
-- When user_id is queried frequently
CREATE INDEX idx_events_user_id
ON events ((payload->>'user_id'));

-- Include the cast when querying it as a number
CREATE INDEX idx_events_user_id_int
ON events (((payload->>'user_id')::INTEGER));
```

For frequent point queries on a specific field, a B-tree index may be more efficient than GIN.

---

## jsonb_path_query — JSONPath Searches

PostgreSQL 12 and later support more flexible searches through **JSONPath** syntax.

```sql
-- Events where action is "error" and severity is at least 3
SELECT *
FROM   events
WHERE  payload @? '$.action ? (@ == "error") && $.severity ? (@ >= 3)';

-- Extract values with jsonb_path_query
SELECT jsonb_path_query(payload, '$.metadata.ip')
FROM   events
WHERE  source = 'api';
```

---

## Aggregation

### Grouping by a Field

```sql
SELECT payload->>'action'    AS action,
       COUNT(*)              AS cnt
FROM   events
GROUP  BY payload->>'action'
ORDER  BY cnt DESC;
```

### jsonb_agg / jsonb_object_agg

```sql
-- Aggregate payloads into an array for each source
SELECT source,
       jsonb_agg(payload ORDER BY occurred_at) AS payloads
FROM   events
GROUP  BY source;
```

---

## Handling Schema Evolution

One advantage of JSONB is the ability to **change the schema later**.

### Adding and Updating Fields

```sql
-- Add a new field to existing rows
UPDATE events
SET    payload = payload || '{"version": 2}'
WHERE  source = 'api';

-- Update a nested field
UPDATE events
SET    payload = jsonb_set(payload, '{metadata, processed}', 'true')
WHERE  id = 42;
```

### Removing Fields

```sql
-- Remove a top-level key
UPDATE events
SET    payload = payload - 'deprecated_field';

-- Remove a nested key
UPDATE events
SET    payload = payload #- '{metadata, tmp}';
```

---

## Performance Design Guidelines

### JSONB vs Relational Columns

JSONB should be used as a tradeoff for flexibility. As a rule, **fields that are fixed and queried frequently should be promoted to relational columns**.

| Situation | Recommendation |
| :--- | :--- |
| Frequently searched or joined | Relational column |
| Fluid schema or highly varied fields | JSONB |
| Writes greatly outnumber reads | JSONB (but use GIN carefully) |
| Full-text or similarity search is required | Separate column + tsvector / pgvector |

### The Cost of GIN Indexes

GIN indexes have a **high write cost**. For workloads with heavy INSERT traffic, consider `fastupdate = off` or limit the index to the fields that need it.

```sql
-- Disable fastupdate to reduce deferred write overhead
CREATE INDEX idx_events_payload ON events
USING GIN (payload) WITH (fastupdate = off);
```

### Verify with EXPLAIN ANALYZE

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM events
WHERE  payload @> '{"action": "error"}';
```

If the plan contains `Bitmap Index Scan on idx_events_payload`, the GIN index is being used. If it shows `Seq Scan`, update statistics with `ANALYZE` or reconsider the query condition.

---

## Combining JSONB with Generated Columns (PostgreSQL 12+)

Fields that require repeated casts are convenient candidates for a **generated column**.

```sql
ALTER TABLE events
ADD COLUMN user_id INTEGER
    GENERATED ALWAYS AS ((payload->>'user_id')::INTEGER) STORED;

CREATE INDEX idx_events_uid ON events (user_id);
```

This preserves JSONB's flexibility while providing fast access to selected fields.

---

## Summary

| Topic | Key Point |
| :--- | :--- |
| **json vs jsonb** | Choose JSONB when search or indexing is required |
| **Operators** | `@>` (containment) and `?` (key existence) are the essentials |
| **Indexes** | Start with GIN; consider B-tree for frequent point queries |
| **Schema evolution** | Append with `||`, update with `jsonb_set`, remove with `-` |
| **Fixed fields** | Promote frequently queried fields to relational columns |
| **Generated columns** | Combine JSONB flexibility with B-tree performance |

Using JSONB as an unrestricted container for everything makes later query optimization difficult. A clear division of responsibility — **relational columns for fixed data and JSONB for variable data** — leads to a design that remains maintainable over time.

---

## References

- [PostgreSQL Documentation — JSON Functions and Operators](https://www.postgresql.org/docs/current/functions-json.html)
- [PostgreSQL Documentation — jsonb Indexing](https://www.postgresql.org/docs/current/datatype-json.html#JSON-INDEXING)
- [Use The Index, Luke — Indexing JSON](https://use-the-index-luke.com/)
