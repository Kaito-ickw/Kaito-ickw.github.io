---
layout: post
title: "Claude Code's /grill-me Skill: Grill Your Design Before Writing Code"
categories: AI Development
tags: ["Claude Code", "Coding Agent", "AI-Native Development", "CLI"]
lang: en
ref: claude-code-grill-me
image:
  path: /assets/images/posts/2026-06-18-claude-code-grill-me/eyecatch.png
  alt: Miniature diorama photo of checking where a road leads before proceeding past a fork
---

A Claude Code skill called "grill-me" has been making the rounds. It ships as part of Matt Pocock's open-sourced `.claude` directory (the mattpocock/skills repository), which has collected over 230,000 stars on GitHub.

The name alone doesn't tell you much. Having dug into it, the purpose comes down to one sentence: before you write any code, have the AI relentlessly interrogate your design.

---

## The Problem /grill-me Solves

When you tell Claude Code to "build X," it starts implementing immediately. If the instruction is ambiguous, the work either changes direction midway or the finished code doesn't match what you meant.

This isn't an AI-specific problem — it's the classic failure mode of starting implementation on underspecified requirements. There's a term for the manual countermeasure: "rubber ducking." You explain your idea to a rubber duck, and the act of articulating it exposes the structure of the problem.

/grill-me automates this — and makes the duck talk back.

---

## How It Works

Usage is simple: invoke `/grill-me` and describe what you want to build in two or three sentences.

The AI takes it from there. The instructions in SKILL.md boil down to three points:

- Relentlessly question every aspect of the plan until shared understanding is reached
- Break the design decision tree down branch by branch, resolving dependencies from upstream first
- Ask one question at a time; offer a recommendation when the answer is clear

"Walking the decision tree branch by branch" is the core of it. A single request like "build this feature" contains many forks — architecture, data model, UX, error handling. /grill-me knocks them down one at a time.

A session runs about 10–45 minutes and ends with a summary of the shared understanding.

---

## Installation

For Claude Code, the skill collection installs as a plugin:

```bash
claude plugins install mattpocock-skills
```

For other agents, or if you want an editable copy, the npx route works too:

```bash
npx skills@latest add mattpocock/skills
```

The npx command installs into your project's `.claude/skills/` directory. Either way, you then invoke it as `/grill-me`.

SKILL.md itself is only a few lines long. The power comes not from a giant prompt but from a clear role instruction: "interrogate thoroughly" and "one question at a time."

---

## When to Use It

The more complex the feature, the more it pays off. If "build this" has only one plausible interpretation, skip it. The more room for interpretation, the more the grilling is worth.

Cases where it fits:

- Feature work spanning multiple files
- Architecture decisions
- "Just build something" requests where the premises are fuzzy

It's unnecessary for simple fixes and bug patches. It's a tool for the stage where the design premises aren't settled yet.

---

## /grill-me vs. /grill-with-docs

A derivative skill, /grill-with-docs, came later. The core behavior is the same, but it reads your existing codebase before asking questions.

For new projects or the initial design of a feature, use /grill-me. When the codebase has matured and you want a design grounded in the existing implementation, /grill-with-docs is the better fit.

---

## References

- [mattpocock/skills - GitHub](https://github.com/mattpocock/skills) ── source of the skill definitions
- [My 'Grill Me' Skill Went Viral - aihero.dev](https://www.aihero.dev/my-grill-me-skill-has-gone-viral) ── Matt Pocock's own write-up
- [Getting Started with Claude Code Skills]({% post_url 2026-06-10-claude-code-skills-guide-en %}) ── overview of the skills mechanism
