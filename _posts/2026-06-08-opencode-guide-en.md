---
layout: post
title: "What is opencode ── An Open-Source AI Coding Agent for the Terminal"
subtitle: Architecture, usage, and how it compares to Claude Code — from the team behind SST
categories: Development
tags: ["opencode", "AI", "coding agent", "CLI", "OSS", "Claude", "LLM"]
lang: en
ref: opencode-guide
---

Terminal-based AI coding tools are multiplying fast.
GitHub Copilot, Cursor, Claude Code, Aider… they all share the same idea — call an LLM from the terminal or editor and edit code — but their design choices differ significantly.

**opencode** is an open-source AI coding agent published in 2025 by the SST (Serverless Stack) team.

- TUI (Text User Interface) that runs entirely in the terminal
- Swap between Claude, GPT, Gemini, and other major LLMs
- MIT license — fully open source
- Agentic loop that reads and writes files and executes shell commands autonomously

This article covers opencode's overview, installation, usage, and how it compares to Claude Code.

---

## The short version

opencode sits closest to "an open-source Claude Code."

```
No vendor lock-in   → works with Claude, GPT-4o, Gemini, and more
Terminal-native     → no VS Code or Cursor required; runs over SSH too
File editing focus  → the agent creates, edits, and runs commands autonomously
OSS                 → read the source, fork it, customize it
```

---

## The problem opencode solves

AI coding tools have a vendor lock-in problem.

- Cursor's UI is tightly coupled to OpenAI / Anthropic
- Claude Code requires an Anthropic API key
- GitHub Copilot is embedded in the GitHub ecosystem

opencode targets teams and developers who need to **choose or switch providers freely** — because the company's security policy only allows one vendor, or because cost optimization means using Gemini Flash for some tasks and Claude Opus for others.

---

## Architecture overview

opencode's runtime breaks into three layers.

```
┌────────────────────────────────────────┐
│  TUI layer (Bubble Tea / Go)           │  ← what you interact with
└───────────────┬────────────────────────┘
                │
┌───────────────▼────────────────────────┐
│  Agent loop                            │  ← LLM calls + tool execution, repeated
│  · read / write files                  │
│  · run shell commands                  │
│  · search / grep                       │
└───────────────┬────────────────────────┘
                │
┌───────────────▼────────────────────────┐
│  Provider abstraction                  │  ← Claude / GPT / Gemini etc.
└────────────────────────────────────────┘
```

### TUI layer

Built with **Bubble Tea**, a Go TUI framework. A chat window, diff preview, and file tree are rendered in the terminal — keyboard-only navigation.

### Agent loop

After receiving an LLM response, opencode checks for tool calls (`read_file`, `write_file`, `bash`, etc.), executes them, and feeds the result back. This loop is the same pattern used by Claude Code and Aider.

### Provider abstraction

All LLMs are called through a unified interface. Switching providers is as simple as editing the config file.

```json
// ~/.config/opencode/config.json
{
  "provider": "anthropic",
  "model": "claude-sonnet-4-5"
}
```

---

## Installation

### macOS / Linux (recommended)

```bash
curl -fsSL https://opencode.ai/install | bash
```

### npm

```bash
npm install -g opencode-ai
```

### Build from source

```bash
git clone https://github.com/sst/opencode
cd opencode
go build ./...
```

---

## Basic usage

### Start

```bash
# open current directory as project
opencode

# specify a directory
opencode /path/to/project
```

Launching opens the TUI chat interface.

### Key bindings

| Key       | Action                         |
|-----------|-------------------------------|
| `Enter`   | Send message                  |
| `Ctrl+C`  | Interrupt running agent        |
| `Ctrl+N`  | Start a new session            |
| `Ctrl+L`  | Clear screen                  |
| `Tab`     | File autocomplete             |
| `?`       | Show help                     |

### Switching provider and model

Use slash commands mid-session.

```
/model claude-opus-4-5
/model gpt-4o
/model gemini-2.0-flash
```

### Referencing files

Use `@` to include files in the conversation.

```
Fix the bug in @src/api/users.py
Read @README.md and summarize this project
```

---

## opencode vs Claude Code

Both tools are "terminal AI coding agents," so they get compared constantly.

| Aspect              | opencode                          | Claude Code                  |
|--------------------|-----------------------------------|------------------------------|
| Providers           | Multiple (Claude, GPT, Gemini…)   | Anthropic only               |
| License             | MIT (OSS)                         | Proprietary                  |
| Language            | Go                                | TypeScript / Node.js          |
| TUI framework       | Bubble Tea (Go)                   | ink (React/Node.js)           |
| MCP support         | Yes (experimental)                | Yes (production-grade)       |
| Custom tools        | Fork and modify                   | hooks / MCP extensions       |
| Cost                | Free (API fees apply)             | Requires Pro plan            |
| Update cadence      | Community-driven                  | Managed by Anthropic         |

**Choose opencode when:**

- You want to control which LLM you use
- You want to read and understand the source code
- Your org only allows specific providers
- You don't want to pay for an Anthropic subscription

**Choose Claude Code when:**

- You want the latest Anthropic models as fast as possible
- You need stable, mature MCP integration
- You rely on Anthropic's support and release cadence

---

## Real-world examples

### Example 1: Implementing a new feature

```
Add JWT authentication.
The current auth code is in @src/auth/.
```

opencode reads the files, installs the needed packages, writes the implementation, and adds tests — all in one agent loop.

### Example 2: Bug fixing

```
There's a KeyError on line 42 of @src/api/users.py.
Stack trace:
KeyError: 'email'
```

The agent reads the file, identifies the root cause, and presents a fix. You approve before it's applied.

### Example 3: Code review

```
Review the diff under @src/ and flag any security issues.
```

---

## Project instructions file

Claude Code has `CLAUDE.md` for project-specific agent instructions. opencode uses **`AGENTS.md`** or **`opencode.md`** placed at the project root.

```markdown
<!-- opencode.md -->
## Project overview
FastAPI + PostgreSQL backend API.

## Coding conventions
- Type hints required (Python 3.11+)
- Format with Ruff
- Tests use pytest

## Notes
- DB migrations managed by Alembic
- .env.production must never be committed
```

---

## Current limitations

opencode is under active development but still has rough edges.

**Stability**
- Large file edits can overflow the context window
- Tool execution reliability is reported as slightly lower than Claude Code

**MCP support**
- Improving but not as mature as Claude Code's implementation
- Complex MCP workflows still favor Claude Code

**Ecosystem**
- Third-party plugins and integrations are sparse
- English documentation is improving; other languages have little coverage

---

## Summary

opencode is a strong option for developers who want an LLM-agnostic, open-source terminal agent — particularly when vendor lock-in is a real constraint.

Pick opencode when:
- You want to use Claude without being tied to Anthropic's toolchain
- You need the flexibility to swap models based on cost or policy
- You want to read and modify the source

Pick Claude Code when:
- You want the deepest Anthropic integration (MCP, hooks, Pro plan)
- Production-grade stability matters more than flexibility

Both tools share the same vision: let an agent write code in the terminal on your behalf. The right choice depends on your constraints.
