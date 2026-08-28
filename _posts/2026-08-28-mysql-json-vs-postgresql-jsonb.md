---
layout: post
title: "MySQL の JSON と PostgreSQL の JSONB の違いと使い分け"
subtitle: 保存形式・演算子・インデックス・部分更新の比較
categories: データエンジニアリング
tags: ["PostgreSQL", "JSONB", "MySQL", "データベース", "SQL"]
lang: ja
image:
  path: /assets/images/posts/2026-08-28-mysql-json-vs-postgresql-jsonb/eyecatch.png
  alt: 同じ形の小包の列を、仕切りの決まった棚と網目状のアーカイブが左右から受け止める切り紙コラージュ
---

MySQL にも PostgreSQL にも JSON 型がある。どちらも「JSONを検証して格納し、パスで取り出し、インデックスも張れる」と説明されるので、一見同じ機能に見える。ただ、実際に設計へ落とすと、インデックスの考え方と更新の内部動作がかなり違う。両方を扱う案件でこの差を整理したので、選定・移行の観点でまとめておく。

なお PostgreSQL 側の基本（演算子・GIN・設計指針）は[PostgreSQL JSONB 完全ガイド]({% post_url 2026-06-05-postgresql-jsonb-guide %})に書いた。この記事は MySQL との差分に絞る。

---

## 結論を先に

| 観点 | MySQL (8.4 LTS / 9.x) | PostgreSQL (18) |
| :--- | :--- | :--- |
| 型 | `JSON` の1種類 | `json` と `jsonb` の2種類 |
| 保存形式 | 独自バイナリ形式に変換 | `jsonb` はバイナリ分解格納（`json` はテキストのまま） |
| 検索の主な手段 | `JSON_EXTRACT` 系関数 + パス文字列 | 演算子（`@>`・`?` など）+ jsonpath |
| インデックス | 生成カラム経由 + 配列専用のマルチバリューインデックス | GIN で文書全体を汎用にカバー |
| 部分更新 | あり（インプレース部分更新） | なし（値全体を書き換え） |
| 行変換 | `JSON_TABLE`（8.0+） | `JSON_TABLE`（17+）・`jsonb_to_recordset` |

最大の違いはインデックスだ。PostgreSQL は「とりあえず GIN を張れば任意のキーで検索できる」のに対し、MySQL は「どのパスで検索するかを決めてから、そのパス用のインデックスを張る」。柔軟スキーマの旨味をどこまでインデックスで支えられるかが分かれる。

---

## 保存形式と検証

MySQL の `JSON` 型は、挿入時に構文を検証したうえで独自のバイナリ形式へ変換して格納する。つまり PostgreSQL でいう `jsonb` に近い動きが標準で、テキストのまま保存する選択肢はない。

PostgreSQL は `json`（テキスト保存）と `jsonb`（バイナリ分解格納）の2択だが、検索やインデックスを使うなら実質 `jsonb` 一択になる。この判断基準は完全ガイドに書いたとおりだ。

どちらもキー順序は保存時に正規化され、入力どおりの順序は保持されない。順序に意味を持たせた JSON を扱う場合は、どちらの DB でも設計を見直した方がよい。

---

## クエリの書き方 ── 同じ記号で中身が違う

紛らわしいのは、両方に `->` と `->>` があることだ。

```sql
-- MySQL: 引数は JSON パス文字列
SELECT payload->'$.user.name'  FROM events;   -- JSON として取得
SELECT payload->>'$.user.name' FROM events;   -- 文字列として取得

-- PostgreSQL: 引数はキー名または添字（1段ずつ）
SELECT payload->'user'->>'name' FROM events;
SELECT payload #>> '{user,name}' FROM events; -- パスでまとめて指定
```

MySQL の `->` は `JSON_EXTRACT()` の短縮記法で、引数に `'$.a.b'` 形式のパス文字列を取る。PostgreSQL の `->` はキーを1段ずつ辿る演算子で、パスで一気に取りたい場合は `#>` / `#>>` か jsonpath を使う。コードを移植するときに最初に踏む差がここになる。

包含検索も対になる書き方がある。「この JSON を含むか」は MySQL では `JSON_CONTAINS(payload, '{"status": "active"}')`、PostgreSQL では `payload @> '{"status": "active"}'` と書く。表現力はおおむね対等で、書き味の好みの範囲だ。

行への展開は、MySQL が先行して持っていた `JSON_TABLE` を PostgreSQL も 17 で標準実装した。SQL/JSON 標準への収束が進んだことで、この領域の差は以前より小さくなっている。

---

## インデックス ── 設計思想が分かれる本丸

**PostgreSQL** は `jsonb` カラムに GIN インデックスを1本張ると、文書内の任意のキー・値の包含検索がインデックスを使える。「どのフィールドで検索するか決まっていない」段階でも、とりあえず検索性能を確保できるのが強みだ。

**MySQL** には JSON カラム全体を汎用にカバーするインデックスがない。取れる手は2つ。

1. **生成カラム経由**: 検索したいパスを生成カラムとして切り出し、そこへ通常のインデックスを張る（`CAST` を使った関数インデックスも同じ発想）
2. **マルチバリューインデックス**（8.0.17+）: JSON 配列の要素を対象にした専用インデックス。`MEMBER OF`・`JSON_CONTAINS`・`JSON_OVERLAPS` がインデックスを使えるようになる

つまり MySQL では「どのパスで検索するか」を設計時に決める必要がある。決まっているなら生成カラム＋B-Tree は高速で、実務上の不足はない。決まっていない・増えていくなら、パスごとにインデックスを足し続けることになり、PostgreSQL の GIN との運用差が開いていく。

裏を返すと、PostgreSQL の GIN は書き込みコストと引き換えの汎用性なので、検索パスが固定的なワークロードでは MySQL 方式（= PostgreSQL でも式インデックスや生成カラム）の方が軽い。この構図は完全ガイドの「JSONB vs リレーショナルカラム」の判断と地続きだ。

---

## 部分更新 ── MySQL が優位な数少ない領域

JSON の一部だけを書き換えるケースでは、内部動作が対照的になる。

- **MySQL** は 8.0 から、`JSON_SET` などによる更新を条件付きで**インプレースの部分更新**として実行できる。バイナリログにも差分だけを書く最適化があり、大きな文書の一部を頻繁に更新するワークロードに効く
- **PostgreSQL** の `jsonb_set` は、値全体を作り直して行を書き換える。文書が大きいほど更新コストが膨らむ

「数百KBの JSON の1フィールドを高頻度で更新する」ような使い方が中心なら、MySQL の方が素直に速い。PostgreSQL でこれをやるなら、更新頻度の高いフィールドを別カラムへ切り出す設計で回避することになる。

---

## 使い分けの指針

DB 自体を JSON 機能だけで選ぶ場面は実際には少ない。既に使っている DB の JSON 機能を正しく使う、が出発点になる。そのうえで:

- **検索パスが事前に決まらない・柔軟スキーマが主役** → PostgreSQL。GIN の汎用性がそのまま効く
- **検索パスが固定的で、更新が多い** → MySQL でも不足はない。生成カラム＋インデックスを最初から設計に入れる
- **大きな文書の部分更新が多い** → MySQL の部分更新が効く。PostgreSQL ならフィールド分離で設計回避
- **移行・併用** → `->` の意味が違うことと、`JSON_CONTAINS` ⇄ `@>` の読み替えを押さえれば、大半のクエリは機械的に書き換えられる

---

## まとめ

MySQL の JSON は「パスを決めて張るインデックス」と「部分更新」、PostgreSQL の JSONB は「決めずに張れる GIN」と「演算子・jsonpath の表現力」。同じ JSON 対応でも、前者は検索パスが既知のワークロード、後者は柔軟スキーマそのものを主役にするワークロードに寄せて作られている。どちらを使うにしても、頻繁に検索する固定フィールドをカラムへ昇格させる原則は共通だ。

---

## 参考

- [MySQL 8.4 Reference Manual ── The JSON Data Type](https://dev.mysql.com/doc/refman/8.4/en/json.html)
- [MySQL 8.4 Reference Manual ── Functions That Search JSON Values](https://dev.mysql.com/doc/refman/8.4/en/json-search-functions.html)
- [PostgreSQL Documentation ── JSON Types](https://www.postgresql.org/docs/current/datatype-json.html)
- [PostgreSQL Documentation ── JSON Functions and Operators](https://www.postgresql.org/docs/current/functions-json.html)
- [PostgreSQL 18.0 Release Notes](https://www.postgresql.org/docs/release/18.0/)
