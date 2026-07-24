---
layout: post
title: "Getting Started with Claude Code Skills"
subtitle: How the slash-command sub-agents work and what they are good for
categories: AI Development
tags: ["Claude Code", "AI-Native Development", "Coding Agent", "CLI"]
lang: en
ref: claude-code-skills-guide
---

Claude Code has a feature called Skills. Invoke one with a slash command and a purpose-built sub-agent spins up to do the work for you.

It would not be surprising if you have never used them. Claude Code does not really advertise the feature — most people discover it either by typing `/` and noticing the list, or by reading the docs. This article walks through what Skills are, how they work, and what you can actually do with them.

---

## What Skills Are

A Skill is a sub-agent with its own system prompt and tool set, narrowed to a specific purpose.

A normal Claude Code conversation talks to a general-purpose model. When you invoke a Skill, a separate agent starts up with instructions and tools dedicated to that task. What sets it apart from an ordinary conversation is that it does not pollute your conversation context and can make more specialized decisions.

Usage is simple: type `/skill-name` in the chat box. Skills that take arguments accept them in the form `/skill-name argument`.

```
/code-review
/code-review --fix
/verify
/loop 5m /code-review
```

---

## A Tour of the Available Skills

The Skills fall into a few categories.

### Code Quality

| Skill | Purpose |
| :--- | :--- |
| `/code-review` | Reviews the current diff and points out bugs and improvements |
| `/simplify` | Proposes and applies refactors to the changed code |
| `/security-review` | Reviews the changes from a security angle |

`/code-review` changes its behavior based on arguments.

```
/code-review          # Report only
/code-review --fix    # Automatically fix the issues it finds
/code-review --comment  # Post inline comments on the GitHub PR

# Depth control
/code-review low      # High-confidence findings only (fewer)
/code-review ultra    # Deep multi-agent review in the cloud
```

`ultra` runs in the cloud rather than locally. It costs money, so keep that in mind, but it is a good fit for a final check on a large changeset.

### Runtime Verification

| Skill | Purpose |
| :--- | :--- |
| `/verify` | Runs the app for real and checks that the change behaves as intended |
| `/run` | Launches the app and verifies behavior while watching the screen |

`/verify` is for confirming that a feature actually works, not whether the tests pass. Code correctness and feature correctness are different things, and this is useful for catching cases where the tests are green but the thing does not work.

### Configuration and Initialization

| Skill | Purpose |
| :--- | :--- |
| `/init` | Generates a new CLAUDE.md |
| `/update-config` | Changes settings.json, adds Hooks, and so on |
| `/keybindings-help` | Customizes keybindings |
| `/fewer-permission-prompts` | Adds frequently used commands to the allowlist to cut down on confirmation dialogs |

`/update-config` is what you use to set up recurring automation as Hooks, such as "run X every time I do Y." Instructing Claude Code within a conversation will not carry over to the next session, but writing it into settings.json makes it persistent.

`/fewer-permission-prompts` quietly pays off. It automatically detects the Bash commands and MCP tools you use often and generates an allowlist. Fewer confirmation dialogs noticeably changes the pace of work.

### Repetition and Scheduling

| Skill | Purpose |
| :--- | :--- |
| `/loop` | Runs a command repeatedly at a given interval |
| `/schedule` | Creates an agent that runs on a schedule in the cloud |

`/loop` is handy for polling, like waiting on CI to finish or confirming a deployment.

```
/loop 5m /verify        # Run verify every 5 minutes
/loop                   # No interval (the model paces itself)
```

### Review and Reference

| Skill | Purpose |
| :--- | :--- |
| `/review` | Reviews a PR |
| `/claude-api` | Looks up Claude API models, pricing, and parameters |

`/claude-api` is for checking things when picking a model or implementing against the API. LLM-related information changes quickly, and asking a model whose training data is stale tends to produce mistakes, so having a dedicated Skill that pulls current information helps.

### Plugin Skills (Vercel)

In environments where the Vercel CLI is installed, Skills with the `vercel:` prefix become available.

```
/vercel:deploy          # Preview deployment
/vercel:deploy prod     # Production deployment
/vercel:status          # Check deployment status
/vercel:env             # Manage environment variables
```

The appeal is being able to run infrastructure operations from the chat, but note that a production deploy runs without a confirmation prompt.

---

## Where to Start

You do not need to use all of them at once. The realistic approach is to start with the ones that give the most benefit for the least side effect.

**The ones that tend to feel worth adding right away:**

1. `/fewer-permission-prompts` — run it once and the confirmation dialogs drop off. The experience changes
2. `/code-review` — make it a habit before committing and you catch fewer things in the diff
3. `/code-review --fix` — when you want the findings and the fixes in one pass

**The ones to reach for once you are comfortable:**

4. `/verify` — hand feature verification to the agent
5. `/loop` — for workflows that need polling or periodic checks
6. `/update-config` — when you want to automate something with Hooks

`ultra` reviews and `/schedule` involve cost and design, so it is fine to leave them until you are used to the everyday uses.

---

## Adding Skills to Your Own Project

You can also create project-specific Skills. Put a Skill definition file in the `.claude/` directory and it becomes a slash command that only works inside that project.

For example, you could create a `/preflight` Skill that runs your project's pre-deploy checks in one shot. Defining a recurring set of steps as a Skill makes it easier to hand off and share.

---

## Summary

| Category | Representative Skill | Purpose |
| :--- | :--- | :--- |
| Code quality | `/code-review` | Diff review and auto-fix |
| Verification | `/verify` | Confirming a feature actually works |
| Configuration | `/update-config` | Persisting Hooks and permission settings |
| Efficiency | `/fewer-permission-prompts` | Cutting confirmation dialogs |
| Repetition | `/loop` | Polling and scheduled runs |
| Infrastructure | `/vercel:deploy` | Deployment operations |

There is plenty you can do in a normal Claude Code conversation, but Skills start up with context and tools tailored to their purpose, and that difference shows in quality. The more a task repeats — code review, runtime verification — the more you gain by handing it to a Skill.

Trying `/fewer-permission-prompts` and `/code-review` first is a good place to start.

---

## References

- [What Is Harness Engineering]({% post_url 2026-06-08-harness-engineering-guide %}) — the bigger picture of Hooks and permission design
- [Building a Multi-Agent Setup as a Solo Developer]({% post_url 2026-06-10-solo-dev-multi-agent-setup %}) — agent design combined with Skills
- [Claude Code Skills Documentation](https://docs.anthropic.com/en/docs/claude-code/skills) — official docs
</content>
</invoke>
