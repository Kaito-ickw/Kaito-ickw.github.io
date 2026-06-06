---
layout: post
title: "なぜフロントエンドに Vercel を選ぶのか ── Netlify・Cloudflare Pages との比較 (2026年版)"
subtitle: AI ネイティブなログアプリのフロントエンド選定
categories: 開発
tags: ["Vercel", "Netlify", "Cloudflare", "Next.js", "フロントエンド", "ホスティング"]
---

[バックエンド選定の記事]({% post_url 2026-06-06-supabase-vs-railway-comparison %})では `フロントエンド → Vercel` と一言で済ませたが、これにも選定理由がある。

フロントエンドのホスティングは **Vercel / Netlify / Cloudflare Pages** の三つ巴になっており、それぞれトレードオフが違う。この記事では 2026年6月時点の最新情報をもとに整理する。

---

## 結論を先に

| 条件 | 選ぶべきサービス |
| :--- | :--- |
| Next.js App Router を使う | **Vercel** 一択に近い |
| 静的サイト・帯域コストを極限まで下げたい | **Cloudflare Pages** |
| Jamstack・フォーム等の組み込み機能が欲しい | **Netlify** |
| 今回のログアプリ (Next.js + AI機能) | **Vercel** |

---

## 各サービスの概要

### Vercel ── Next.js の本家

Next.js を作った Vercel 社のホスティングサービス。
フレームワークとプラットフォームが一体設計されているため、App Router の高度な機能が**設定なしで動く**のが最大の強み。

2025〜2026年の主要アップデート：

- **Fluid Compute** 導入：サーバーレス関数がウォームを保ち、複数リクエストを並列処理。コールドスタートを大幅削減。
- **AI Gateway** 統合：OpenAI / Anthropic 等へのルーティング・コスト追跡がダッシュボードから可能。
- **非 US リージョンのレイテンシ改善**：2025年比で p99 レイテンシが約 25% 向上。

#### 料金 (2026年6月時点)

| プラン | 月額 | 主な内容 |
| :--- | :--- | :--- |
| **Hobby** | $0 | 100GB 転送、関数 100万回/月、商用利用不可 |
| **Pro** | $20/ユーザー | 1TB 転送、Edge リクエスト 1,000万回、商用利用可 |
| **Enterprise** | 要相談 | SAML SSO、SLA 99.99%、専任サポート |

> Pro の帯域超過は $0.15/GB。Edge ミドルウェアは**全プラン無料**。

---

### Cloudflare Pages ── コストと速度のチャンピオン

Cloudflare の 300+ エッジロケーションを活かした静的ホスティング。
**帯域が実質無制限** ($5/月の Workers プランに含まれる) なのが圧倒的な差別化点。

- エッジは V8 Isolates を使用 → コールドスタートほぼゼロ (< 1ms)
- 2026年に Docker コンテナサポートを追加 → Node.js 完全互換へ前進
- **OpenNext** アダプターの成熟で Next.js App Router の大部分が動作するように

#### Vercel との比較でのデメリット

- ISR (Incremental Static Regeneration) の一部挙動が Vercel と異なる
- Server Actions や Next.js 独自の最適化機能の完全対応は Vercel に遅れる
- AI Gateway 等 Vercel 独自エコシステムとの統合がない

#### 料金

| プラン | 月額 |
| :--- | :--- |
| **Pages Free** | $0 (帯域・リクエスト数は無制限) |
| **Workers Pro** | $5 (Pages + Workers の全機能) |

帯域 1TB/月 の場合、Vercel Pro が $150 程度になるのに対し Cloudflare Pages は $5 固定。**コスト差は数十倍になりうる。**

---

### Netlify ── Jamstack の老舗

静的サイトジェネレーター時代のリーダーだったが、2026年現在は Vercel・Cloudflare と比べてパフォーマンス・コスト両面で見劣りする。

- **Form・Identity・Analytics** などのオールインワン機能は競合より充実
- Build Plugin エコシステムが成熟
- グローバルの平均レイテンシは 3 サービス中最も高い

#### 料金

| プラン | 月額 |
| :--- | :--- |
| **Free** | $0 (100GB 帯域) |
| **Pro** | $19/ユーザー |
| **Enterprise** | 要相談 |

---

## 三つを並べて比較

| | Vercel | Cloudflare Pages | Netlify |
| :--- | :---: | :---: | :---: |
| **Next.js 完全対応** | ✅ | ⚠️ (ほぼ対応) | ⚠️ (ほぼ対応) |
| **エッジパフォーマンス** | ◎ (改善中) | ◎ (最速クラス) | △ |
| **帯域コスト** | ⚠️ (高め) | ✅ (無制限) | ⚠️ |
| **コールドスタート** | ◎ (Fluid Compute) | ✅ (V8 Isolates) | △ |
| **AI 機能統合** | ✅ (AI Gateway) | ❌ | ❌ |
| **Preview URL** | ✅ PR ごと自動 | ✅ | ✅ |
| **無料枠の商用利用** | ❌ | ✅ | ✅ |
| **月額最低 (有料)** | $20/ユーザー | $5 | $19/ユーザー |

---

## なぜ今回は Vercel を選ぶのか

ログアプリの具体的な要件で判断する。

### ① Next.js App Router を使う

Server Components・Server Actions・Streaming を最大限活用したい。
Cloudflare Pages の OpenNext 対応は成熟しつつあるが、**Vercel 以外でのトラブル対応コストが読めない**という実際的なリスクがある。個人開発でこのリスクを取りに行く必要はない。

### ② AI 機能との統合

Vercel AI Gateway を使うと、複数 LLM プロバイダーへのルーティング・レート制限・コスト追跡がワンストップで管理できる。ログアプリがAIを呼ぶ場面 (ログの要約・異常検知など) では、この統合が効いてくる。

### ③ プレビュー URL でのチーム確認

PR のたびにプレビュー URL が自動生成される機能は三者とも持っているが、Vercel のそれが最も成熟している。バックエンド (Supabase / Railway) の環境切り替えとの連携も簡単。

### ④ 帯域コスト問題について

Vercel Pro の 1TB を超えると $0.15/GB かかるのは事実で、高トラフィックになると課題になる。ただしログアプリのフロントエンドが帯域 1TB を超える規模は「Phase 3〜4」の話。その段階になったら Cloudflare Pages + OpenNext への移行を改めて検討すればよい。

---

## スケールに合わせた見直し軸

バックエンド記事と同様に、フロントエンドのスイッチングも規模に合わせて考えておく。

| フェーズ | 推奨 | 理由 |
| :--- | :--- | :--- |
| **個人・検証** | Vercel Hobby (無料) | 商用でなければ無料で全機能使える |
| **有料化・チーム** | Vercel Pro ($20/人〜) | 商用利用のため。Preview URLや分析も使える |
| **帯域 1TB を安定的に超えてきた** | Cloudflare Pages に移行を検討 | コスト差が数十倍になるため |
| **エンタープライズ / コンプライアンス** | Vercel Enterprise | SLA・SAML SSO・専任サポートが必要なら |

---

## まとめ

Next.js + AI 機能の組み合わせで個人〜スモールチームが開発するなら **Vercel は現状ベストな選択肢**。
コストが問題になってくる規模になったら Cloudflare Pages への移行パスは現実的になっており、2026年時点でその移行難易度は下がっている。

Netlify は特定の組み込み機能 (Forms / Identity 等) が必要なケース以外では選ぶ積極的な理由が薄くなっている。

---

## 参考情報

- [Vercel Pricing](https://vercel.com/pricing)
- [Vercel vs Netlify vs Cloudflare Pages 2026 — DevToolReviews](https://www.devtoolreviews.com/reviews/vercel-vs-netlify-vs-cloudflare-pages-2026)
- [Vercel vs Netlify vs Cloudflare Pages — Vibe Coder Blog](https://blog.vibecoder.me/vercel-vs-netlify-vs-cloudflare-pages)
- [Cloudflare Pages vs Netlify vs Vercel 2026 — DanubeData](https://danubedata.ro/blog/cloudflare-pages-vs-netlify-vs-vercel-static-hosting-2026)
- [Vercel Cost 2026 — makerkit.dev](https://makerkit.dev/blog/saas/vercel-cost)
