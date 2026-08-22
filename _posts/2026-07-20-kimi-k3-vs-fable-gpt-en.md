---
layout: post
title: "Kimi K3 vs Claude Fable 5 vs GPT-5.6 Sol: Frontier Model Comparison (2026)"
subtitle: Where the largest open-weight model actually stands
date: 2026-07-20 09:00:00 +0900
categories: AI Development
tags: ["AI", "LLM", "OSS"]
lang: en
ref: kimi-k3-vs-fable-gpt
last_modified_at: 2026-08-22
image:
  path: /assets/images/posts/2026-07-20-kimi-k3-vs-fable-gpt/eyecatch.png
  alt: Risograph-style race illustration of two sealed boats being caught by a larger boat with an exposed frame
---

Moonshot AI announced Kimi K3 on July 16, 2026. "Fable-class" is the verdict you see thrown around on social media — but is it? This post sorts out whose model it is and what it's actually better and worse at than Claude Fable 5 and GPT-5.6 Sol, based on public benchmarks and third-party evaluations. The comparison reflects the situation as of July 20, 2026; an update note at the end covers what has changed since.

## What Is Kimi K3?

Kimi K3 is the flagship model from Moonshot AI (月之暗面), a Chinese startup that stands alongside DeepSeek as one of the leading Chinese AI companies. The Kimi series ships in three forms: web app, API, and open weights.

K3's key specs:

- 2.8 trillion total parameters — the largest open-weight model ever released at announcement time
- 1M-token context window
- Kimi Delta Attention (KDA) with a LatentMoE architecture: 16 of 896 experts active, with roughly 2.5× the scaling efficiency of K2
- Model weights were published on July 27, 2026 (HuggingFace: moonshotai/Kimi-K3)

Reaching the frontier while staying open-weight is what got the launch treated as a second DeepSeek moment.

## Benchmark Standings

Moonshot's own framing is "beats Claude Opus 4.8 and GPT-5.5, but falls short of Claude Fable 5 and GPT-5.6 Sol overall" — and the third-party evaluation from Artificial Analysis lands on roughly the same conclusion.

| Metric | Kimi K3 | GPT-5.6 Sol | Claude Fable 5 |
| :--- | :--- | :--- | :--- |
| AA Intelligence Index | 57.1% | 58.9% | **59.9%** |
| FrontierSWE (coding) | **77.8** | 77.6 | 76.8 |
| Frontend Code Arena | **#1 (1,679)** | ─ | #2 |
| GDPval v2 (knowledge work) | 1,668 | ─ | **1,760** |
| GPQA Diamond | 93.5% (best open-weight) | ─ | ─ |

![Horizontal bar chart comparing Kimi K3, GPT-5.6 Sol, and Claude Fable 5 on AA Intelligence Index, FrontierSWE, and GDPval v2. The three models are within a few percent on every metric; Fable 5 leads overall while K3 leads in coding. No published GDPval v2 figure for GPT-5.6 Sol](/assets/images/posts/2026-07-20-kimi-k3-vs-fable-gpt/benchmark-comparison-en.svg){: .chart}

Across the 14 benchmarks both vendors report in common, Fable 5 wins 8 and K3 wins 6. Fable 5 leads overall, but it is not a one-sided gap.

Broken down by domain, the pattern is clear:

- **Coding**: K3 tops FrontierSWE and Frontend Code Arena. For coding specifically, "Fable-class" is not an exaggeration
- **Knowledge work**: On GDPval v2 the gap to Fable 5 is 92 points — the widest among the metrics where both compete
- **Weak spot**: Hallucination rate reportedly worsened from 39% in the previous generation to 51%. Accuracy went up, but so did the frequency of confidently wrong answers

## Pricing

| Model | Input ($/1M tokens) | Output ($/1M tokens) |
| :--- | :--- | :--- |
| Kimi K3 | 3 | 15 |
| GPT-5.6 Sol | 5 | 30 |
| Claude Fable 5 | 10 | 50 |

![Horizontal bar chart comparing input and output prices per million tokens for Kimi K3, GPT-5.6 Sol, and Claude Fable 5. Input is $3, $5, and $10; output is $15, $30, and $50. K3 is roughly one third the price of Fable 5](/assets/images/posts/2026-07-20-kimi-k3-vs-fable-gpt/pricing-comparison-en.svg){: .chart}

K3 costs about one third of Fable 5 — but it is also a steep increase from the previous-generation K2.6 ($0.95 / $4), putting it at the same level as Claude Sonnet 5. It has been read as a signal that the "Chinese AI = dirt cheap" assumption is starting to break down. One estimate puts the measured cost per task at about $0.94, on par with GPT-5.6 Sol.

## Verdict

"Fable-class" is half right. Coding and agentic tasks: on par with or better than Fable 5. Overall intelligence and knowledge-work quality: one tier below. Price: one third. And open weights are a kind of value the proprietary duo cannot offer. As an option that doesn't depend on the two proprietary leaders, it is well worth trying in production.

## Update (August 22, 2026)

The landscape has moved since July. Artificial Analysis revised its index (v4.1.1, August 20), where K3 now scores 60 — still the top open-weight model, tied with GLM-5.3. Newer frontier models have also shipped since, including Claude Opus 5, so the table above should be read as a snapshot of the July frontier rather than the current leaderboard. K3's API pricing is unchanged at $3 / $15.

## References

- [Moonshot releases 2.8-trillion-parameter Kimi K3 (Tom's Hardware)](https://www.tomshardware.com/tech-industry/artificial-intelligence/moonshot-releases-2-8-trillion-parameter-kimi-k3)
- [Kimi K3, and what we can still learn from the pelican benchmark (Simon Willison)](https://simonwillison.net/2026/Jul/16/kimi-k3/)
- [Kimi's open model K3 nears GPT-5.6 Sol and Fable 5 (The Decoder)](https://the-decoder.com/kimis-open-model-k3-nears-gpt-5-6-sol-and-fable-5-while-signaling-the-end-of-super-cheap-chinese-ai/)
- [China's Moonshot AI unveils Kimi K3 (CNBC)](https://www.cnbc.com/2026/07/17/moonshot-ai-kimi-k3-model-openai-anthropic-china.html)
- [Kimi K3 Benchmarks (BenchLM)](https://benchlm.ai/models/kimi-k3)
