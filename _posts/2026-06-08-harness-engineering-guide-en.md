---
layout: post
title: "What Is Harness Engineering? Designing the Environment Your AI Agent Runs In"
subtitle: Designing and implementing Hooks, the Ralph Loop, and the Supervisor Pattern in Claude Code
categories: AI Development
tags: ["Harness Engineering", "AI Agent", "Claude Code", "Ralph Loop", "Automation", "AI-Native Development"]
lang: en
ref: harness-engineering-guide
---

Use AI agents in real development long enough and you hit a turning point.

**The problem isn't that the model isn't smart. It's that the design for *how you make the model work* hasn't caught up.**

- The agent makes changes to files you never intended
- It loops and repeats the same failure
- It deletes tests and calls the run a "success"
- It calls external services without approval
- You can't trace what it actually did

None of these are model problems. They come from not designing the *constraints, information, and evaluation* that surround the model.

This design area is called **Harness Engineering**.

---

## The Short Answer

Harness engineering is **the discipline of designing and controlling the execution environment an AI agent runs in**.

You could call it the work of building the "outside" of the model.

```
Inside the harness (the enclosure)
  ↓ Control the information (what it sees)
  ↓ Control the actions (what it can do)
  ↓ Evaluate the result (judge what was actually accomplished)
```

The main ways harness engineering gets implemented are as follows.

| Mechanism | Role |
| :--- | :--- |
| CLAUDE.md / AGENTS.md | Static instructions and context injected into the agent |
| Hooks | Script intervention at lifecycle events |
| Permission model | Allow, deny, or confirm tool execution |
| Tool surface | The range of tools exposed to the agent |
| Agent loop design | Control over when and how it repeats |

> As of 2026, after companies put AI agents into production, the industry has started to share a realization: getting the "enclosure" right is harder than making the model smarter.

---

## What Is a Harness?

The word "harness" originally came from software testing. A "test harness" is what runs the code under test inside a controlled environment.

When applied to AI agents, the meaning broadens.

**It refers to the system that controls the entire environment the model runs in ── what it can see, what it can do, and what it returns.**

Take Claude Code as an example. What the user touches directly is the "model," but around it sits a structure like this.

```
┌──────────────────────────────────────────────┐
│  Harness                                        │
│  ┌─────────────────────────────────────────┐  │
│  │  CLAUDE.md / AGENTS.md                   │  │
│  │  (instructions / context for the agent)  │  │
│  ├─────────────────────────────────────────┤  │
│  │  Hooks                                   │  │
│  │  (PreToolUse / PostToolUse / Stop etc.)  │  │
│  ├─────────────────────────────────────────┤  │
│  │  Permissions                             │  │
│  │  (tool execution policy)                 │  │
│  ├─────────────────────────────────────────┤  │
│  │  Tool Surface                            │  │
│  │  (range of exposed tools)                │  │
│  └─────────────────────────────────────────┘  │
│                    ↕                            │
│           [ Model / LLM ]                       │
│                    ↕                            │
│  ┌─────────────────────────────────────────┐  │
│  │  Evaluation                              │  │
│  │  (tests / traces / human-in-the-loop)    │  │
│  └─────────────────────────────────────────┘  │
└──────────────────────────────────────────────┘
```

The model runs inside this harness. Without one, the model operates in a state where it can see anything and do anything.

---

## The Three-Layer Architecture of a Harness

As of 2026, practical harness design is organized into three layers.

### Layer 1: Information Layer

The layer that controls **what the agent sees**.

- Which past information is included in the context
- Which tools are exposed (including their schemas)
- What you teach it up front via CLAUDE.md or AGENTS.md
- Context compression and filtering

Much of an agent's reasoning quality is decided here. Building good context is far more effective than refining the prompt.

### Layer 2: Action Layer

The layer that controls **what the agent does**.

```
Plan → Tool Call → Guardrail Check → Parse → Retry or Complete
```

The core of this layer is agent loop design. How many times it repeats, under what conditions it stops, and what happens on failure.

Hooks belong to this layer. PreToolUse can block a specific operation, and PostToolUse can record the result to a log.

### Layer 3: Evaluation Layer

The layer that **judges what was actually accomplished**.

- Automatic verification via tests, lint, and type checks
- Tracing (a record of what the agent saw and did)
- Human-in-the-loop (human confirmation and approval)

Without an evaluation layer, there's no way to confirm whether the agent really did what it says it did.

---

## Implementation Element 1: CLAUDE.md and AGENTS.md

### CLAUDE.md

A configuration file Claude Code loads automatically. Placing it at the project root injects it into the agent's context at the start of a session.

```markdown
# Project overview
This project uses Python 3.11 / FastAPI / PostgreSQL.

# Development conventions
- Use pytest for tests
- Use Black for code formatting
- Type annotations are required (mypy strict)
- Manage migrations with Alembic

# How to run
- Start dev server: `docker compose up`
- Run tests: `pytest`
- Apply migrations: `alembic upgrade head`

# Cautions
- Never run a direct DROP against the database
- Do not edit production config files
- Never commit secrets.env
```

What's written in CLAUDE.md doesn't need to be repeated in every prompt. It's the single place to manage what the agent "should know."

### AGENTS.md

Where CLAUDE.md is specific to Claude Code, AGENTS.md is a convention for a broader set of agent tools. When multiple agents (Claude Code, Codex, and so on) use the same repository, it works as the place for cross-tool instructions.

The key difference: **CLAUDE.md is instructions, while AGENTS.md leans more toward being an agreement between agents.**

```markdown
# AGENTS.md

## Role division between agents
- architect (Claude Code): task design, review, merge decisions
- backend (Codex): implementation of API, DB, and tests

## Communication protocol
- On task completion: `DONE <task-id> -> architect`
- When blocked: `BLOCKED <task-id> by <reason>`
- Review findings: `CHANGES <task-id> -> backend`

## Commands that must never run
- git push --force
- DROP TABLE / DROP DATABASE
- rm -rf (outside the workspace)
```

---

## Implementation Element 2: Hooks

Claude Code's Hooks are a mechanism for injecting shell scripts or HTTP endpoints into the agent's lifecycle events.

### Main hook events (as of June 2026)

| Event | Timing |
| :--- | :--- |
| `PreToolUse` | Just before tool execution |
| `PostToolUse` | Just after tool execution |
| `PostToolUseFailure` | Just after a tool execution fails |
| `Stop` | Just before the agent stops |
| `SessionStart` | At session start |
| `UserPromptSubmit` | Just after the user submits a prompt |
| `SubagentStart / SubagentStop` | Subagent start / stop |

### Why PreToolUse Matters

**PreToolUse is the strongest line of defense in a harness.**

The "do not do this" you wrote in CLAUDE.md can be overridden at the model's discretion. But if you exit a PreToolUse hook with exit code `2`, the tool call is blocked **unconditionally**. Code beats instructions.

```bash
#!/bin/bash
# pre_tool_use.sh
# PreToolUse hook: block dangerous commands

TOOL_NAME="$1"
TOOL_INPUT="$2"

if [ "$TOOL_NAME" = "Bash" ]; then
  # Block git push --force
  if echo "$TOOL_INPUT" | grep -qE 'git\s+push\s+.*--force'; then
    echo "BLOCKED: git push --force is not allowed" >&2
    exit 2
  fi

  # Block rm -rf
  if echo "$TOOL_INPUT" | grep -qE 'rm\s+-rf\s+/'; then
    echo "BLOCKED: rm -rf against root is not allowed" >&2
    exit 2
  fi

  # Block access to secrets files
  if echo "$TOOL_INPUT" | grep -qE '\.env\.prod|secrets\.env'; then
    echo "BLOCKED: access to production secrets files is not allowed" >&2
    exit 2
  fi
fi

exit 0
```

Register the hook in Claude Code's `settings.json`.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "bash /path/to/pre_tool_use.sh"
          }
        ]
      }
    ]
  }
}
```

### Using the Stop Hook

Use the Stop hook when you want to run something at the moment the agent finishes its work.

```bash
#!/bin/bash
# stop_hook.sh
# Run tests when the agent stops to check quality

echo "=== Agent stopped → running tests automatically ===" >&2
cd "$PROJECT_ROOT"

# Run tests
if ! pytest --tb=short -q 2>&1; then
  echo "WARNING: tests are failing" >&2
fi

# Formatting check
if ! black --check . 2>/dev/null; then
  echo "WARNING: some files need Black formatting" >&2
fi
```

---

## Implementation Element 3: The Permission Model

Claude Code's permission model controls what operations the agent can run in three tiers.

| Setting | Behavior |
| :--- | :--- |
| Auto-allow (allowlist) | Runs without confirmation |
| Manual confirmation (default) | Asks the user for confirmation |
| Block (denylist) | Refuses to run |

You can tune it finely in `settings.json`.

```json
{
  "permissions": {
    "allow": [
      "Bash(git status)",
      "Bash(git diff*)",
      "Bash(pytest*)",
      "Bash(black*)",
      "Read(*)"
    ],
    "deny": [
      "Bash(git push --force*)",
      "Bash(rm -rf*)",
      "Bash(curl* --upload*)"
    ]
  }
}
```

The **principle of least privilege** is the baseline here too. Give the agent only the permissions the current task needs. Grant broadly during development, and narrow it in environments closer to production.

---

## Implementation Pattern 1: The Ralph Loop

The Ralph Loop is a pattern that **runs the agent repeatedly, letting it work autonomously until a goal condition is met**.

The name comes from Ralph Wiggum, a character in the animated series *The Simpsons* — after the way he innocently tries the same thing over and over. It started as a community pattern devised by Geoffrey Huntley, and was later officially implemented as Claude Code's `/goal` command.

### The Core Idea of the Ralph Loop

A normal agent runs once and stops. The Ralph Loop works on this idea.

```
1. Define the goal condition (exit condition)
2. Run the agent for one turn (with fresh context)
3. Check the goal condition (tests, lint, a marker file, etc.)
4. If not met, return to step 2
5. If met, finish
```

The crucial part is "with fresh context." Resetting the context each time prevents "context rot" during long runs. State is persisted to the filesystem or git, and reconstructed by reading it back on the next turn.

### A Minimal Shell-Script Implementation

```bash
#!/usr/bin/env bash
# ralph.sh ── a loop that runs Claude Code repeatedly

GOAL_FILE="GOAL.md"         # file describing the goal condition
PROGRESS_FILE="progress.md" # file for progress state
MAX_ITERATIONS=20           # maximum number of iterations
ITERATION=0

# Goal-check function (customize to fit your project)
check_goal() {
  # Are all tests passing?
  pytest --tb=no -q 2>&1 | grep -q "passed" || return 1
  # Is lint clean?
  ruff check . --quiet 2>&1 | grep -q "^$" || return 1
  return 0
}

while [ $ITERATION -lt $MAX_ITERATIONS ]; do
  ITERATION=$((ITERATION + 1))
  echo "=== Iteration $ITERATION / $MAX_ITERATIONS ==="

  # Check goal achievement
  if check_goal; then
    echo "✓ Goal reached. Ending the loop."
    exit 0
  fi

  # Have it rebuild context by reading git log and the progress file
  PROMPT="$(cat "$GOAL_FILE")

Current state:
$(cat "$PROGRESS_FILE" 2>/dev/null || echo '(no progress yet)')

Recent commits:
$(git log --oneline -5)

Test status:
$(pytest --tb=short -q 2>&1 | tail -20)

Given the state above, take the next step toward the goal.
When done, append what you did to progress.md."

  # Run Claude Code in headless mode for one turn
  claude --print "$PROMPT"

  # Short wait (to respect API rate limits)
  sleep 3
done

echo "Reached the maximum number of iterations. Please check manually."
exit 1
```

### An Example GOAL.md

```markdown
# Goal conditions

All of the following must be satisfied.

1. `pytest` passes all tests
2. `ruff check .` passes with no errors
3. `black --check .` reports everything is formatted
4. The auth endpoints `/auth/login` and `/auth/logout` are implemented
5. The OpenAPI documentation is updated

When the goal is reached, create a progress.md that contains only `DONE`.
```

---

## Implementation Pattern 2: The /goal Command (Official Implementation)

`/goal` is the official Claude Code implementation of the Ralph Loop. Introduced around the end of 2025, it achieves the loop without a shell script.

### Basic Usage

```
/goal <completion condition> (max 4000 characters)
```

```
/goal
The auth API implementation must be complete.
Conditions:
- pytest passes all tests
- /auth/login and /auth/logout are implemented
- All type annotations are present
- The API documentation is updated
```

When you run it, Claude Code behaves like this.

```
1. Remember the goal condition
2. Do the work as usual
3. At the end of each turn, a dedicated lightweight model evaluates the goal condition
4. If unmet, start the next turn
5. If met, clear the goal and stop
```

Unlike the shell script, **the goal evaluation is done by a model**. It's a judgment made by an LLM, not by running code. This is both a strength and a weakness. Conditions that can be judged mechanically in code (tests passing, lint clean) are more reliably judged by a script, but judgments like "is it implemented appropriately?" are something an LLM is better at.

| Trait | `/goal` | Shell-script Ralph Loop |
| :--- | :--- | :--- |
| Setup effort | Nearly zero | Requires writing a script |
| Goal evaluation | Judged by an LLM | Can be judged mechanically in code |
| Customization | Limited | Free |
| Reproducibility | Somewhat low | High |
| Best fit | Qualitative completion conditions | Quantitative conditions (tests, etc.) |

---

## Implementation Pattern 3: The Supervisor Pattern

The **Supervisor Pattern** is a structure where a higher-level agent (the Supervisor) directs, reviews, and approves the work of lower-level agents (Workers).

```
Supervisor (Claude / orchestrator)
  ├─ Worker A (Codex / backend)  ← task implementation
  ├─ Worker B (agy / reviewer)   ← review
  └─ Worker C (specialist)       ← specific domain
```

The Supervisor's role is as follows.

- Define tasks and assign them to Workers
- Receive Workers' deliverables and review them
- Send work back if it doesn't meet the quality bar
- Integrate the work of multiple Workers

The key is the role division: **the Supervisor holds the "judgment," while Workers handle only "execution."** If a Worker autonomously expands the scope of its own judgment, the Supervisor's control stops working.

### Phase-Gating

Phase-gating is a pattern used together with the Supervisor Pattern, placing explicit gates between work phases.

```
Phase 1: DESIGN
  → Gate: architecture approval
Phase 2: IMPLEMENT
  → Gate: tests passing, review approval
Phase 3: INTEGRATE
  → Gate: E2E tests passing
Phase 4: RELEASE
  → Gate: final human confirmation
```

You can't advance to the next phase without passing each gate. This structurally prevents states like "allowed to move to the release phase while the design isn't finished."

Always place a human-approval gate before high-cost operations (production deploys, database changes, and so on).

---

## Implementation Pattern 4: The Circuit Breaker

The **Circuit Breaker** is a pattern that prevents an agent from falling into a "doom loop."

A doom loop is a state where the agent keeps repeating the same failure. When the agent keeps trying the same approach without understanding *why* it's failing, it burns only cost and time.

```
Example of a doom loop:
iteration 1: edit file A → tests fail
iteration 2: edit file A (same approach) → tests fail
iteration 3: edit file A (same approach) → tests fail
... (repeats)
```

### Implementing a Circuit Breaker

```bash
#!/usr/bin/env bash
# circuit_breaker.sh

FAILURE_LOG="/tmp/agent_failures.log"
MAX_CONSECUTIVE_FAILURES=3
SAME_FILE_EDIT_LIMIT=5

# Count consecutive edits to the same file
check_edit_count() {
  local file="$1"
  local count
  count=$(grep -c "EDIT:$file" "$FAILURE_LOG" 2>/dev/null || echo 0)
  if [ "$count" -ge "$SAME_FILE_EDIT_LIMIT" ]; then
    echo "CIRCUIT_OPEN: edits to $file have reached $count" >&2
    echo "Consider a different approach. Human judgment may be needed." >&2
    exit 2  # block as a PreToolUse hook
  fi
  echo "EDIT:$file" >> "$FAILURE_LOG"
}

# Count consecutive failures
check_failure_count() {
  local count
  count=$(grep -c "FAIL:" "$FAILURE_LOG" 2>/dev/null || echo 0)
  if [ "$count" -ge "$MAX_CONSECUTIVE_FAILURES" ]; then
    echo "CIRCUIT_OPEN: $count consecutive failures" >&2
    echo "BLOCKED: manual confirmation required" >&2
    exit 2
  fi
}
```

When the Circuit Breaker trips, the agent hands the task back to a human as `BLOCKED`. As a design choice, "reporting that it's stuck" is more correct than "pushing on regardless."

---

## Principles of Harness Design

We've looked at individual implementation mechanisms. Finally, here are the design principles.

### 1. Trust code over instructions

Writing "do not do this" in CLAUDE.md isn't enough. Returning exit code `2` from a PreToolUse hook is more reliable. Instructions can be overridden at the model's discretion; code cannot.

### 2. Start with least privilege

Don't give the agent broad permissions from the start. Grant only "the permissions the current task needs," and widen as necessary. Starting narrow is safer than narrowing later.

### 3. Keep loops finite

Both the Ralph Loop and auto-launch scripts must always set a maximum count and maximum time. A state where "the agent keeps running autonomously" delays detection when something goes wrong.

### 4. Keep evaluation independent of the model

Don't let the model itself judge whether "the tests passed." Run tests, lint, and type checks in an independent process. You need confirmation that it actually succeeded, not a report saying "it succeeded."

### 5. Make sure a human can stop it

For any automation, provide a way for a human to stop it at any time. Even if full automation is the goal, without an emergency stop the damage grows when a problem occurs.

---

## Summary

| Point | Content |
| :--- | :--- |
| **What a harness is** | The design of the execution environment that controls an agent's information, actions, and evaluation |
| **Three-layer structure** | Information layer (what it sees), action layer (what it does), evaluation layer (what was accomplished) |
| **CLAUDE.md** | Static context auto-injected at the start of a session |
| **Hooks** | PreToolUse is the strongest line of defense. Code beats prompts |
| **Ralph Loop** | A pattern that repeats until the goal is reached while resetting context |
| **/goal** | The official implementation of the Ralph Loop. An LLM judges goal achievement |
| **Supervisor Pattern** | A higher-level agent with judgment manages lower-level agents that execute |
| **Circuit Breaker** | Detects a doom loop, stops automatically, and hands back to a human |

Harness engineering isn't "a spellbook for making agents write good code."

It's about **building a structure where, no matter what the agent does, it can't exceed the intended scope.**

The smarter the model gets, the more this structure matters. Because the smarter a model is, the greater its ability to reach a goal in ways you didn't intend. That problem gets a closer look in the sequel.

---

## References

- [Skill Issue: Harness Engineering for Coding Agents](https://www.humanlayer.dev/blog/skill-issue-harness-engineering-for-coding-agents) — a practical write-up by HumanLayer
- [Agent Harness Engineering — The Rise of the AI Control Plane](https://medium.com/@adnanmasood/agent-harness-engineering-the-rise-of-the-ai-control-plane-938ead884b1d) — Adnan Masood on the harness as a control plane
- [AddyOsmani.com — Agent Harness Engineering](https://addyosmani.com/blog/agent-harness-engineering/) — Addy Osmani's explanation of harness engineering
- [The Complete Claude Code Harness Engineering Guide](https://dev.to/shipwithaiio/the-complete-claude-code-harness-engineering-guide-5-layers-8-deep-dives-3d4j) — a 5-layer, 8-deep-dive guide on DEV Community
- [Claude Code Architecture Explained: Six Harness Layers](https://mer.vin/2026/05/claude-code-architecture-explained-six-harness-layers-beyond-the-llm/) — Mervin Praison on Claude's six harness layers
- [Ralph Wiggum Loop and /goal in Claude Code](https://theaiarchitects.com/blog/claude-code-ralph-loop) — a practical explanation of the /goal command and the Ralph Loop
- [GitHub: snarktank/ralph](https://github.com/snarktank/ralph) — the original Ralph implementation repository
- [GitHub: frankbria/ralph-claude-code](https://github.com/frankbria/ralph-claude-code) — a Ralph implementation for Claude Code
- [Claude Code Hooks reference](https://docs.anthropic.com/en/docs/claude-code/hooks) — the official Claude Code Hooks documentation
- [GitHub: ai-boost/awesome-harness-engineering](https://github.com/ai-boost/awesome-harness-engineering) — an Awesome list for harness engineering
