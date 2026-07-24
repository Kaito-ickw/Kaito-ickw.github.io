---
layout: post
title: "Designing an Orchestrator That Keeps Agents Running Autonomously"
subtitle: Why the context problem is asymmetric between worker and orchestrator agents, and the 2026 approaches to solving it
categories: AI Development
tags: ["Multi-Agent", "Context Management", "Claude Code", "Codex CLI", "LLM"]
lang: en
ref: agent-context-management-2026
image:
  path: /assets/images/posts/2026-06-07-agent-context-management-2026/eyecatch.png
  alt: A miniature control room where finished work is moved to an external archive to clear the desk
---

When you try to make an agent carry out many tasks autonomously, you hit an asymmetric problem.

**Worker agents (the implementers)** can end their session every time a task finishes. The next task begins with a blank context. Context-management problems rarely show up.

**Orchestrator agents** don't have that luxury. They need to keep track of what's done, what's left, and what comes next across many tasks, so you want them to stay alive for a long time. But the longer they live, the more context piles up, and eventually the model's behavior starts to shift.

This isn't a question of "when to clear." It's a question of **how you design the orchestrator**. This post summarizes the approaches being used as of June 2026.

---

## Why Long Context Becomes a Problem

"We'll be in trouble if we hit the limit" is a correct concern, but the problem starts well before that.

### Context Rot

Even before the context window fills up, the quality of an LLM's output begins to degrade. This phenomenon came to be called "context rot" over 2025–2026.

A study by ChromaDB covering 18 frontier models confirmed that **output quality drops as the input grows longer, across every model**.

There are three main causes.

**The lost-in-the-middle effect:** transformers attend well to the beginning and end of a context, but attention to the middle thins out. Cases where accuracy drops by more than 30% have been reported.

**The cost of attention computation:** a 100K-token context means 10 billion pairwise relationships. Because processing cost grows quadratically, long contexts tend to lose accuracy across the board.

**Accumulated noise:** the "approaches that didn't work" that pile up during trial and error mislead the model precisely because they're semantically related. For coding agents this is the most troublesome, showing up as "smart but not behaving correctly."

Model context windows keep expanding year over year, but context rot happens regardless of the limit. A larger window defers the problem; it doesn't dissolve it.

---

## The Asymmetry of the Problem

```
Worker agent (e.g. Codex)
  task-001 implement → DONE → end session
  task-002 implement → DONE → end session  ← context resets every time
  task-003 implement → DONE → end session

Orchestrator agent (e.g. Claude orchestrator)
  task-001 issue → receive DONE → review → merge → issue task-002
  task-002 issue → receive DONE → review → CHANGES → wait for fix
  task-003 issue → ...                             ← context keeps accumulating
```

A worker agent can run one session per task. When the task finishes, it ends the session and starts a fresh one for the next task. It resets every time, before the context gets polluted.

An orchestrator can't do that, because "deciding what to do next based on the results of past tasks" is the orchestrator's job.

---

## Three Approaches to Solving It Autonomously

Having "a human judge the timing and clear" is fine, but you can't rely on it if you want more autonomy. The approaches in use as of 2026 fall into three categories.

### Approach 1: Use Subagents to Prevent Context Pollution

Claude Code has a subagent feature. Child agents **run in an independent context window, and their results come back to the parent as a summary**.

```
orchestrator (Claude, long-lived)
  context: [task list, design principles, summaries of completed work, ...]

  → delegate task-002 to a subagent
      subagent context: [task-002 spec, file read results, test run logs, ...]
      ← returns only a summary: "feat/api-v2 implemented, 3 files changed, all tests pass"

  only the summary gets added to the orchestrator context
```

Even if the child agent consumes 100K tokens, only a few hundred tokens of summary land in the parent's context. This is a mechanism for **isolating the worker's context pollution from the parent**.

That said, it doesn't solve "the orchestrator's own context accumulation." The more tasks there are, the more the summaries stack up and the parent grows too. It isn't a fundamental fix, but it greatly slows the rate of growth.

### Approach 2: Design the Orchestrator to Be "Thin" (Ralph Loop)

A pattern called the "Ralph Loop" spread over 2025–2026. The idea is simple.

**Don't hold state in the orchestrator's context. Write all state externally.**

```
while tasks remain:
  1. read current state from the external store (git / agmsg / files)
  2. decide the one thing to do next
  3. delegate it to a worker agent
  4. write the result to the external store
  5. clear the context and return to the start
```

You can clear at the end of each loop **because all the state needed for a decision is written externally**. The context only needs "this round's decision"; it doesn't need to remember past exchanges.

```text
# Traditional (context-dependent)
"That CHANGES thing I sent three conversations ago — what happened to it?"

# Ralph Loop (external-state-dependent)
At loop start: check agmsg inbox
             → detect DONE task-003
             → check the diff with git log
             → make the next decision
```

The agmsg + git setup pairs well with this design. agmsg's message history and git's commit history become the external store for "what's done and what's left."

**An example of implementing autonomous clearing (as an instruction to Claude Code):**

```text
# Written in CLAUDE.md or the system prompt
When one task completes (after receiving DONE and finishing the merge),
before moving to the next task, do the following:
1. Record what was completed in AGENTS.md
2. Run /compact
3. Check the agmsg inbox and pick up the next task
```

By keeping this in context as an instruction to the model, you can get compact called without human intervention. There's no 100% guarantee the model follows the instruction, but because a clear trigger ("task complete") exists, the decision rarely drifts.

### Approach 3: Let the Model Decide When to Compact (OpenCode's Approach)

OpenCode takes an approach where **the model itself calls a `Compress` tool** for this problem.

The model is given a Compress tool and can invoke it on its own at the moment it judges "this task is done, now is a good time to compress." Unlike Claude Code's automatic compaction, which acts as an "emergency measure near the limit," it can fire at a meaningful boundary — the task boundary.

Claude Code currently has no equivalent feature. `/compact` is a manual command, and automatic compaction is an emergency measure at the limit (~95%).

---

## Position Tool-Built-in Compaction as an "Emergency Measure"

The right way to understand tool-built-in compaction is as a fallback for when the design failed to solve the problem.

### Claude Code

As the context approaches the limit, it runs compaction automatically.

- 200K model: triggers around ~167K (~83%)
- Opus [1M] model: triggers around ~367K (a measured value reported on GitHub)
- The threshold can be adjusted with `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`

Compaction is not a simple summary; it generates a structured summary split into nine sections (the session's purpose, completed tasks, pending issues, code changes, and so on). It's also designed to work well with prompt caching, so cache hits are likely even after compaction.

Manual invocation is `/compact`. You can add custom instructions too.

```bash
/compact Omit the details of completed tasks and keep only the unresolved issues
```

### Codex CLI

From v0.128 it introduced a native Memories system (disabled by default).

In-session compaction uses the remote `compact()` endpoint (returned as an AES-encrypted blob) for Codex models, and a local summary for non-Codex models.

```toml
# ~/.codex/config.toml
[memories]
enabled = true
idle_hours_before_extraction = 2
max_thread_age_days = 30
```

When Memories is enabled, it extracts insights in the background after a session ends and automatically injects them at the start of the next session. It's useful for carrying over "this project's coding conventions" and "frequently used patterns."

Every session is stored as JSONL under `~/.codex/sessions/`, and you can return to the previous session with `codex resume --last`.

### OpenCode

In addition to providing the model with a `Compress` tool, it first runs pruning that protects at least the last 40,000 tokens (and 20,000 tokens) until reaching 96–99%. Compaction is designed to be truly a last resort.

---

## Memory Across Sessions: External Memory

Separate from in-session compaction, **memory that spans sessions** requires external memory.

### Letta (formerly MemGPT)

A three-tier structure that mimics an OS memory hierarchy.

```
core memory     ── always in context (equivalent to RAM)
archival memory ── externally searchable vector store (equivalent to disk)
recall memory   ── summaries of conversation history
```

The agent itself manipulates memory by calling tools like `core_memory_append` and `archival_memory_search`. It's a design where the model actively decides "what to remember."

### Mem0

A cross-agent persistent memory layer that doesn't depend on a particular framework. It integrates with the Anthropic SDK, the OpenAI Agents SDK, and the Google ADK. An algorithm update in April 2026 improved the accuracy of temporal queries by +29.6 points.

Because multiple agents can reference the same memory layer, an orchestrator and workers can share project knowledge.

### MCP Memory Servers

Memory servers accessible over MCP from both Claude Code and Codex CLI are growing in number.

| Service | Characteristics |
| :--- | :--- |
| Hindsight | Per-session insight extraction, vector search |
| Basic Memory | A simple Markdown-file-based MCP server |
| Mem0 MCP | Uses Mem0's memory layer over MCP |

**When to introduce external memory:** Mem0 and Letta show their true value in scenarios where you "give a single agent a continuous stream of tasks over several weeks or more" or "want to share project knowledge across multiple agents." In the early phase, using AGENTS.md + agmsg history as the external store has a lower adoption cost.

---

## Checkpoints and Resumption: A Different Dimension of Fault Tolerance

Separate from context management, long-running operation also requires fault tolerance so that "the process can resume even after a crash."

**Google ADK** creates a checkpoint on every tool call, so even if the container crashes it can read the current step and resume. It persists conversation state with `DatabaseSessionService` (SQLite/Cloud SQL) and supports Human-in-the-Loop flows that pause for days.

**Microsoft Agent Framework (BUILD 2026)** provides a mechanism that detects hitting the context limit mid-loop and automatically compacts on the framework side to continue.

---

## Summary: What Solves Which Problem

| Means | Problem it solves | Autonomy |
| :--- | :--- | :--- |
| Subagents (Claude Code) | Isolate the worker's context pollution from the parent | High (solved by design) |
| Ralph Loop (external state + clear loop) | The orchestrator's own context accumulation | High (solved by design) |
| Compact instruction in CLAUDE.md | Autonomous compaction at task boundaries | Medium (model-dependent) |
| OpenCode Compress tool | The model compacts autonomously at the right time | High |
| Claude Code auto-compact | Emergency measure near the limit | High (automatic) |
| Codex CLI Memories | Carry insights across sessions | High (background) |
| Letta / Mem0 | Long-term cross-session, cross-agent memory | High (framework) |
| Google ADK checkpoint | Resume from a process failure | High (framework) |

A dedicated feature for "autonomously compacting the orchestrator at task boundaries" does not exist in Claude Code as of June 2026. OpenCode's Compress tool comes closest to it. To achieve the equivalent in Claude Code, you supplement it with an instruction in CLAUDE.md or a Ralph Loop design.

---

## Applying This to an agmsg + Claude + Codex Setup

If you want to autonomously manage the orchestrator's (Claude's) context in this setup, the following is a realistic design.

**Write in CLAUDE.md (or the system prompt):**

```text
You are an orchestrator collaborating with Codex through agmsg.
Operate in the following loop:

1. Check the agmsg inbox
2. When you receive DONE: git merge, record completion in AGENTS.md, run /compact
3. After /compact: re-check the agmsg inbox and issue the next TASK
4. If a design decision is needed, return BLOCKED and defer to a human
```

**Prepare the external store:**

```text
AGENTS.md
  ├── completed tasks (task-id, branch, summary)
  ├── currently in-progress tasks
  ├── outstanding design decisions
  └── principles and constraints

agmsg message history
  └── the source of truth for task handoffs and results

git commit history
  └── the source of truth for implementation details
```

If Claude reads AGENTS.md at the start of the loop, it can reconstruct "where it is now" even after clearing the context. This is the external state that makes the Ralph Loop work.

---

## Conclusion

Context management for autonomous agents is a design problem more than a tooling problem.

**Worker agents can end their session per task.** This is something you can explicitly choose as a design.

**The orchestrator's problem is asymmetric.** You want it to stay alive for a long time, but the context accumulates. To solve this autonomously:

1. Use **subagents** to isolate the worker's context pollution from the parent
2. Make **the external store the source of truth** so the design can restart even after clearing (Ralph Loop)
3. Use **explicit instructions to the model** to have it compact autonomously at task boundaries

Tool-built-in compaction is an emergency measure near the limit; it's not a substitute for design. External memory (Letta, Mem0) layers on top of this to handle memory across sessions.

The answer to "when to clear" is to **keep the orchestrator in a state where clearing is safe**. You solve the timing problem as a design problem.

---

## References

### Context management and compaction

- [Context Compaction Research: Claude Code, Codex CLI, OpenCode, Amp](https://gist.github.com/badlogic/cd2ef65b0697c4dbe2d13fbecb0a0a5f) — a cross-comparison study of the compaction implementations in major tools
- [Context Compaction Deep Dive: Codex CLI, Claude Code, and OpenCode](https://codex.danielvaughan.com/2026/04/14/context-compaction-deep-dive-codex-cli-claude-code-opencode/) — a detailed comparison of each tool's compaction strategy
- [Context Window Management for Long-Running AI Agents](https://zylos.ai/research/2026-03-31-context-window-management-session-lifecycle-long-running-agents/) — context design for long-running agents
- [Compaction — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/compaction) — Anthropic's official documentation
- [Codex CLI Memories: Native Session Persistence](https://codex.danielvaughan.com/2026/05/01/codex-cli-memories-persistent-context-session-memory-ecosystem/) — details of the v0.128 Memories system

### Context rot

- [Context Rot: Why LLMs Degrade as Context Grows](https://www.morphllm.com/context-rot) — the definition and mechanism of context rot
- [How to Use the /compact Command in Claude Code to Prevent Context Rot](https://www.mindstudio.ai/blog/claude-code-compact-command-context-management) — practical usage

### Orchestrator and subagent design

- [Claude Code Subagents: A 2026 Practical Guide](https://www.tembo.io/blog/claude-code-subagents) — how to use subagents and context separation
- [The Code Agent Orchestra](https://addyosmani.com/blog/code-agent-orchestra/) — Addy Osmani. Patterns for multi-agent coding (including the Ralph Loop)
- [Long-Running Coding Agents: The 2026 Guide](https://o-mega.ai/articles/long-running-coding-agents-the-2026-guide) — a design guide for long-running agents

### External memory and frameworks

- [State of AI Agent Memory 2026](https://mem0.ai/blog/state-of-ai-agent-memory-2026) — a report on the state of agent memory by Mem0
- [Memory for Autonomous LLM Agents](https://arxiv.org/html/2603.07670v1) — an academic overview of agent memory
- [Agent Memory at Scale 2026: Letta, Zep, Mem0, and LangMem Compared](https://agentmarketcap.ai/blog/2026/04/10/agent-memory-vendor-landscape-2026-letta-zep-mem0-langmem) — a comparison of major frameworks

### Checkpoints and long-running workflows

- [Build Long-running AI agents that pause, resume, and never lose context with ADK](https://developers.googleblog.com/build-long-running-ai-agents-that-pause-resume-and-never-lose-context-with-adk/) — Google Developers Blog
- [Microsoft Agent Framework at BUILD 2026](https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-at-build-2026-announce/) — the Agent Harness's context management features
