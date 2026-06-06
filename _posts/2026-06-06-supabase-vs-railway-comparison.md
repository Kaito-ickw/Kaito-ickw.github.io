---
layout: post
title: "Supabase vs Railway vs Neon ── AIネイティブなログアプリのバックエンド選定 (2026年版)"
subtitle: 主要 BaaS/PaaS の最新料金・機能を徹底比較
categories: 開発
tags: ["Supabase", "Railway", "Neon", "BaaS", "PaaS", "バックエンド"]
lang: ja
ref: supabase-vs-railway-comparison
---

AIネイティブなログアプリを個人で開発している。
バックエンドの選定を進める中で **Supabase** と **Railway** のどちらにするか迷い、ついでに **Neon** や **PlanetScale** も候補に挙がってきた。

この記事では 2026年6月時点の最新情報をもとに、各サービスの特徴・料金・ユースケースを整理する。

---

## まず「何を選ぶか」の軸を整理する

ログアプリに求める要件はざっくりこんな感じ。

- **構造化ログの書き込み**（AIエージェントのトレース、ユーザー操作履歴など）
- **リアルタイムor準リアルタイムのクエリ**
- **pgvector によるベクトル検索**（ログの意味検索、類似インシデント検索）
- **個人 → チーム規模へのスケールアップ**
- **月のランニングコストをできる限り抑えたい**

この軸で各サービスを見ていく。

---

## Supabase ── オールインワン BaaS

### 概要

PostgreSQL をコアに据えた **BaaS (Backend as a Service)**。
DB だけでなく Auth・Storage・Realtime・Edge Functions がワンパッケージで揃う。
pgvector はすべてのプランで**無料**で利用可能なのが嬉しいポイント。

### 主な機能

| 機能 | 内容 |
| :--- | :--- |
| データベース | PostgreSQL (フルマネージド) |
| 認証 | メール・OAuth・Magic Link・電話 |
| ストレージ | S3 互換オブジェクトストレージ |
| リアルタイム | WebSocket によるリアルタイムサブスクリプション |
| Edge Functions | Deno ランタイム |
| ベクトル検索 | pgvector 組み込み (無料) |

### 料金 (2026年6月時点)

| プラン | 月額 | 主な制限 |
| :--- | :--- | :--- |
| **Free** | $0 | DB 500MB、プロジェクト2個、MAU 5万 |
| **Pro** | $25〜 | DB 8GB、MAU 10万、ストレージ 100GB |
| **Team** | $599〜 | SOC2/ISO 27001、バックアップ14日 |
| **Enterprise** | 要相談 | HIPAA対応、専用インフラ |

Pro プランは**デフォルトで使用上限あり**なので、予期せぬ請求を防ぎやすい。
コンピュートは別途 $12〜の追加課金。

### ログアプリ視点での評価

- ✅ pgvector が使えるのでベクトル検索をすぐ始められる
- ✅ Auth / Realtime が標準搭載 → 認証周りを自前実装しなくていい
- ✅ Row Level Security (RLS) でマルチテナント対応がしやすい
- ⚠️ コンピュートを上げると費用が一気に跳ね上がる
- ⚠️ Free プランはプロジェクト数・ストレージが少なめ

---

## Railway ── 柔軟な汎用 PaaS

### 概要

コンテナベースで何でもデプロイできる **PaaS (Platform as a Service)**。
Supabase とは競合というより**補完関係**に近い。Next.js や FastAPI などのバックエンドサービス・ワーカーを動かすのが本領。

ビルドシステムは **Nixpacks** を採用しており、Dockerfile を書かなくてもフレームワークを自動検出してくれる。

### 主な機能

| 機能 | 内容 |
| :--- | :--- |
| デプロイ | コンテナ (Nixpacks / Dockerfile) |
| DB | PostgreSQL・MySQL・MongoDB・Redis (マネージド) |
| スケーリング | vCPU・RAM を秒単位課金 |
| テンプレート | OSS を one-click デプロイ |
| CI/CD | GitHub 連携で自動デプロイ |

### 料金 (2026年6月時点)

| プラン | 月額 | 付与クレジット |
| :--- | :--- | :--- |
| **Trial** | $0 (一時) | $5 のワンタイムクレジット |
| **Hobby** | $5 | $5 のリソースクレジット込み |
| **Pro** | $20/シート | $20 のリソースクレジット込み |
| **Enterprise** | 要相談 | SLA・コンプライアンス対応 |

**使い切った分だけ払う**モデル。$5 の Hobby プランなら $3 しか使わなくても $5 の請求、$8 使ったら $8 の請求になる。

### ログアプリ視点での評価

- ✅ FastAPI / Go などのログ収集サービスをそのままコンテナで動かせる
- ✅ キュー (Redis) やワーカーも同一プロジェクト内で管理できる
- ✅ 秒単位課金でアイドル時のコストを節約できる
- ⚠️ BaaS 機能 (Auth/Storage) は自前実装が必要
- ⚠️ pgvector を使うなら自分で拡張をインストールする必要がある

---

## Neon ── サーバーレス PostgreSQL の本命

### 概要

**サーバーレス PostgreSQL** に特化したデータベースサービス。
2025年に Databricks が約10億ドルで買収し、AIエージェント向けのデータ基盤として強化されている。

**ブランチ機能**が特徴で、git のように DB のスナップショットを作成して PR ごとにテスト環境を用意できる。

### 主な機能

| 機能 | 内容 |
| :--- | :--- |
| データベース | PostgreSQL (サーバーレス) |
| スケール | オートスケーリング + ゼロスケール |
| ブランチ | DB の git ブランチ機能 |
| エッジ対応 | HTTP ドライバーでエッジから直接クエリ |
| pgvector | 対応 |

### 料金 (2026年6月時点)

| プラン | 月額 | 主な制限 |
| :--- | :--- | :--- |
| **Free** | $0 | 0.5GB、コンピュート 10h |
| **Launch** | $19〜 | 10GB、コンピュート無制限 |
| **Scale** | $69〜 | 50GB、コンプライアンス機能 |

### ログアプリ視点での評価

- ✅ ゼロスケールで個人開発フェーズのコストを最小化
- ✅ Databricks 傘下でAI連携が強化される方向
- ✅ ブランチ機能でスキーマ変更のテストが楽
- ⚠️ コールドスタートがある (ゼロスケール時に数秒の遅延)
- ⚠️ Supabase と違い Auth/Storage は別途用意が必要

---

## PlanetScale ── エンタープライズ向け MySQL/Postgres

### 概要

Vitess ベースの**高スケール DB サービス**。Cursor・Intercom・Block など大規模サービスの実績がある。
**2024年に無料プランを廃止**し、エンタープライズ寄りのポジションに舵を切った。

### 料金 (2026年6月時点)

| プラン | 月額 |
| :--- | :--- |
| **Hobby** | $39〜 |
| **Scaler** | $79〜 |
| **Enterprise** | 要相談 |

個人開発・初期フェーズには料金的に重い。大規模・ミッションクリティカルなユースケースに向いている。

---

## Render ── Railway に近い汎用 PaaS

Railway の対抗馬として言及されることが多い。
Web サービス・ワーカー・DB・Static Site をまとめて管理できる。

- Free プランあり (750h/月のコンピュート)
- PostgreSQL マネージド対応
- Auto-deploy from GitHub

Railway に比べると設定の自由度はやや低いが、UI がシンプルで初心者には取っつきやすい。

---

## 比較まとめ

| | Supabase | Railway | Neon | PlanetScale | Render |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **カテゴリ** | BaaS | PaaS | DBaaS | DBaaS | PaaS |
| **DB** | PostgreSQL | PostgreSQL 等 | PostgreSQL | MySQL/PG | PostgreSQL 等 |
| **Auth** | ✅ 標準搭載 | ❌ 自前 | ❌ 自前 | ❌ 自前 | ❌ 自前 |
| **pgvector** | ✅ 無料 | ⚠️ 手動 | ✅ 対応 | ❌ MySQL主体 | ⚠️ 手動 |
| **ゼロスケール** | ❌ | ✅ | ✅ | ✅ | ✅ (Free のみ) |
| **無料枠** | ✅ 500MB | ✅ $5 | ✅ 0.5GB | ❌ | ✅ 750h |
| **月額最低 (有料)** | $25 | $5 | $19 | $39 | $7〜 |
| **個人開発向け** | ◎ | ◎ | ○ | △ | ○ |
| **チーム・本番向け** | ○ | ○ | ○ | ◎ | ○ |

---

## 今回カバーしなかったが候補になりうるサービス

今回比較した 5 サービスは「PostgreSQL・クラウドホスト型・個人〜チーム規模」という軸では現状デファクトに近いが、要件次第では以下も検討に値する。

| サービス | カテゴリ | 外した理由 / 検討すべきケース |
| :--- | :--- | :--- |
| **Firebase** | BaaS (NoSQL) | NoSQL・モバイルファーストなら第一候補。ログを Firestore に入れるとクエリ柔軟性が低く今回は外した |
| **Fly.io** | PaaS | Railway より細かいリージョン制御が可能。グローバル展開・レイテンシ重視になったら移行候補 |
| **Convex** | BaaS (TypeScript ネイティブ) | TypeScript でサーバーロジックを書くとリアルタイムクエリが自動更新される独自モデル。2025〜2026年で急速に注目を集めている |
| **Appwrite** | BaaS (セルフホスト) | OSS でベンダーロックインを避けたいチーム向け。クラウド版もあるが Supabase に比べるとエコシステムが小さい |
| **Cloudflare Workers + D1** | エッジ PaaS + DBaaS | 圧倒的に安い (帯域無制限 $5/月〜)。ただし SQL 機能が限定的でログの複雑なクエリには今は厳しい |
| **Turso** | DBaaS (エッジ SQLite) | libSQL をグローバルに分散。読み取り重視のグローバルキャッシュ層として面白いが、書き込み集中なログ用途とは相性がやや悪い |

まとめると：**PostgreSQL + クラウドホスト + pgvector + 個人〜スタートアップ規模** という前提なら今回の 5 サービスの比較で選定できる。モバイルファースト・セルフホスト・エッジ特化など別の軸が加わると Firebase / Fly.io / Cloudflare が浮上する。

---

## スケールに合わせた判断軸

サービスを選んだあとも、規模が変わるたびに見直しのタイミングが来る。おおよその目安として残しておく。

### Phase 1｜個人開発・検証フェーズ (〜$30/月)

```
ログ収集 API     → Railway (Hobby / $5)
DB + Auth        → Supabase (Free)
```

無料枠の範囲で動かし切ることを優先。Supabase Free の 500MB と Railway の $5 クレジットで十分走れる。

**見直しトリガー:** Supabase の DB が 500MB に近づく or MAU が 5万を超えそうになった時点で Pro へ。

---

### Phase 2｜有料ユーザーが来た・チーム 2〜5人 ($50〜$120/月)

```
ログ収集 API     → Railway (Pro / $20/シート)
DB + Auth        → Supabase (Pro / $25〜)
```

Supabase Pro でバックアップ・接続数・MAU 上限が緩和される。コンピュートは最小 (Micro $12/月) で様子を見る。

**見直しトリガー:** API のレスポンスが遅くなってきた or DB のコンピュートがボトルネックと分かった時。

---

### Phase 3｜本格グロース・チーム 10 人前後 ($200〜$500/月)

この段階で「Auth だけ Clerk に外出し」「DB のみ Neon に移行」などレイヤー分割が有効になってくる。

```
ログ収集 API     → Railway (Pro) or Fly.io (リージョン最適化)
DB               → Supabase Pro (大容量) or Neon Scale (ブランチ・分析活用)
Auth             → Supabase Auth のまま or Clerk に移行
ベクトル検索      → pgvector のまま or 専用ベクトル DB (Qdrant 等) を検討
```

Neon のブランチ機能で「本番 DB のクローンをステージングに使う」運用が効いてくるのもこのフェーズ。

**見直しトリガー:** チームが DB マイグレーションの管理で詰まり始めたら Neon のブランチ機能が本領を発揮するタイミング。

---

### Phase 4｜エンタープライズ・コンプライアンス対応 ($500+/月)

```
DB               → Supabase Team ($599〜 / SOC2・ISO27001) or PlanetScale Enterprise
Auth             → Supabase Auth + SAML or Auth0 / Okta
ログ収集 API     → Railway Enterprise or 自社 Kubernetes
```

PlanetScale の真価は Cursor・Intercom レベルの書き込みスループットが必要になった時。初期から選ぶ理由はない。

**見直しトリガー:** 顧客からコンプライアンス証明書 (SOC2 レポート等) を要求されたタイミング。

---

## 私の結論：Supabase + Railway の組み合わせが本命

今回開発している AI ネイティブなログアプリの要件を踏まえると、こんな構成が現実的だと思っている。

```
フロントエンド (Next.js)    → Vercel
ログ収集 API (FastAPI)      → Railway
DB + Auth + ベクトル検索     → Supabase (pgvector)
```

フロントエンドに Vercel を選んだ理由は[別記事]({% post_url 2026-06-06-vercel-frontend-selection %})で詳しく解説している。

**Supabase 単体**でもある程度の API は Edge Functions で動かせるが、ログ収集のような**常時稼働・高スループット**なワークロードはコンテナで動かす Railway の方が向いている。

**Neon** は Databricks 傘下になりAIとの親和性が高まっており、将来的にログ分析パイプラインと統合する可能性を考えると注目しておきたいサービス。ただし Auth や Storage を自前で用意する必要があるため、初期フェーズは Supabase に軍配が上がる。

---

## 参考情報

- [Supabase Pricing](https://supabase.com/pricing)
- [Railway Pricing Docs](https://docs.railway.com/pricing/plans)
- [Neon vs Supabase — Bytebase](https://www.bytebase.com/blog/neon-vs-supabase/)
- [Best Backend Platforms for Indie Hackers 2026 — MindStudio](https://www.mindstudio.ai/blog/best-backend-platforms-indie-hackers)
- [Supabase vs PlanetScale vs Neon 2026 — DevToolReviews](https://www.devtoolreviews.com/reviews/supabase-vs-planetscale-vs-neon)
- [Railway vs Supabase — UI Bakery](https://uibakery.io/blog/railway-vs-supabase)
