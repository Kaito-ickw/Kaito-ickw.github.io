---
layout: post
title: "Building a Multi-Agent Setup as a Solo Developer"
subtitle: Splitting roles, designing communication, and using Git worktrees
categories: AI Development
tags: ["Multi-Agent", "Claude Code", "Codex", "agmsg", "AI-Native Development", "Coding Agent", "Automation"]
lang: en
ref: solo-dev-multi-agent-setup
---

The word "multi-agent" tends to conjure an image of a large team running some massive system. But a design that runs several agents holds up perfectly well for solo development too. In fact, being solo is exactly why it pays to make the division of roles explicit and lower your own decision-making cost.

This post lays out how to think about the design when building a multi-agent setup as a solo developer, along with concrete configuration patterns.

---

## The Short Answer

A multi-agent setup for solo development rests on three elements.

1. **Separation of roles** — split the orchestrator (design, review, integration) from the implementer
2. **Communication design** — define the message paths between agents
3. **Your own position** — the human acts as PM. You don't write code; you approve and decide

Full automation is the eventual endpoint, but you don't have to aim for it from the start. The realistic beginning is a three-way split of labor: "Claude + Codex + you."

---

## Why Multi-Agent Helps Even for Solo Development

When you use AI agents alone, the natural starting style is "hand everything to Claude Code." That isn't a bad approach. But past a certain scale, it hits limits.

- The context grows long, and the agent's output quality starts to degrade
- Design and coding get mixed into the same agent, blurring the roles
- It becomes hard for you to grasp "what is actually progressing"

The biggest reason to go multi-agent is context separation. The orchestrator keeps track of "what's done and what's left." The implementer ends its session when a task is finished and starts the next task from a blank slate. This structure alone dramatically reduces the context rot of long development sessions.

The details are covered in [Context Design for Keeping Agents Running Autonomously]({% post_url 2026-06-07-agent-context-management-2026 %}).

---

## Designing the Roles

If you're starting with a minimal setup, two roles are enough.

```
orchestrator (Claude Code)
  role: task definition, design review, decisions about merging to main
  context: maintained over the long term

implementer (Codex)
  role: implementing APIs, DBs, and tests
  context: reset per task
```

The orchestrator decides "what to do," and the implementer executes "how to do it." As long as this separation works, the implementer's context stays light even while the orchestrator carries a long conversation history.

If you're solo but also want machine review, one option is to add a one-shot reviewer. It doesn't need to run as a resident process — handing it a diff and running it once is enough.

---

## Designing the Communication

When you run several agents, you need to decide where the information about "what was done and what finished" is shared.

The simplest approach is file-based. Put a task list in `tasks.md` and have each agent read and write it. No additional infrastructure is required, and git keeps the history.

```markdown
# tasks.md

## In Progress
- [ ] task-001: Implement the /auth/login endpoint [backend]

## Done
- [x] task-000: Design the DB schema [architect]
```

When you need dedicated messaging, one option is **agmsg**. It's an inter-agent messaging layer built on SQLite — no network required, and it stays self-contained inside a devcontainer. Messages are sent and received in this format.

```text
DONE    task-001 -> architect Implementation complete, tests pass
CHANGES task-001 -> backend  Please add error handling
BLOCKED task-001 by         DB connection config value unknown
```

That said, once you start using agmsg, an asymmetric handoff problem appears: "how does Codex receive a CHANGES from Claude?" I laid out that problem and the patterns that resolve it in detail in [The Asymmetric Handoff Problem Between Claude and Codex, and How to Solve It]({% post_url 2026-06-07-multi-agent-asymmetric-handoff %}).

Starting file-based and migrating to agmsg once a bottleneck appears wastes the least effort.

---

## Designing Git Worktrees

When multiple agents work in parallel on the same repository, having them work on the same branch causes conflicts. To prevent this, use worktrees.

```bash
# Create a dedicated worktree for each agent
git worktree add .worktrees/backend feat/auth-api
git worktree add .worktrees/review  review/auth-api
```

The structure looks like this.

```
.
├── (main worktree: main / the orchestrator's workspace)
└── .worktrees/
    ├── backend/   ← where Codex implements
    └── review/    ← for review (if needed)
```

When a task is finished, the orchestrator checks the diff and merges it into main. You can recreate worktrees per task, or fix them to roles and keep reusing them.

Worktrees have one more benefit. Because you can physically separate each agent's working area, accidents like "Codex mistakenly overwrites a file on main" become far less likely. From a harness design standpoint, filesystem-level separation is a powerful safety mechanism.

---

## The Human's Role: Act as PM

In this setup, the role the solo developer takes on is no longer writing code.

- Define tasks and hand them to the orchestrator (Claude)
- Make decisions on the CHANGES and BLOCKED that the orchestrator surfaces
- Check the diff and merge once implementation is complete
- Check the agmsg inbox periodically

A real day flows like this.

```
Morning:
  Check tasks.md
  → tell the orchestrator "what to do today"
  → the orchestrator splits the tasks and assigns them to Codex

During work:
  Decide when a CHANGES/BLOCKED comes from the orchestrator
  Check the diff when Codex completes a task

Evening:
  Have the orchestrator write a summary before ending the session
  → use it to rebuild context the next morning
```

The most important thing in this workflow is to treat BLOCKED lightly. Codex reporting "I don't know" is not a failure. Deferring to the human when a design decision is needed is correct behavior. The state where "Codex keeps implementing while confused" is far more of a problem.

---

## Guaranteeing Safety with a Harness

A design that runs agents autonomously can't do without safety mechanisms. At minimum, put the following settings in place.

Block dangerous commands with a `PreToolUse` hook.

```bash
#!/bin/bash
# pre_tool_use.sh
TOOL_INPUT="$2"
if echo "$TOOL_INPUT" | grep -qE 'git\s+push\s+.*--force'; then
  echo "BLOCKED: git push --force is forbidden" >&2
  exit 2
fi
if echo "$TOOL_INPUT" | grep -qE 'DROP\s+(TABLE|DATABASE)'; then
  echo "BLOCKED: DROP is forbidden" >&2
  exit 2
fi
exit 0
```

Use Claude Code's permission settings to auto-allow read-only operations and require confirmation for operations with side effects.

```json
{
  "permissions": {
    "allow": ["Read(*)", "Bash(git status)", "Bash(git diff*)"],
    "deny":  ["Bash(git push --force*)"]
  }
}
```

The full picture of harness design is laid out in [What Is Harness Engineering?]({% post_url 2026-06-08-harness-engineering-guide %}).

---

## Start Incrementally

Trying to build the whole thing at once makes the design cost high. In practice, it's better to assemble it step by step.

**Step 1: Two agents + file-based communication**

Make Claude Code the orchestrator and Codex the implementer, and share tasks through `tasks.md`. Start without agmsg and without worktrees. You launch Codex manually.

**Step 2: Separate with worktrees**

Move Codex's workspace into a worktree. This alone prevents accidental writes to the main branch.

**Step 3: Receive notifications with a lightweight watcher**

Introduce agmsg and run a lightweight watcher that detects DONE/BLOCKED. Launching Codex can stay manual.

**Step 4: Launch with approval**

Set it up so that when the watcher notifies you, Codex launches once you approve in a confirmation dialog.

If you get Step 2 or 3 working, that's often plenty for solo-development productivity. Anything beyond Step 4 you can think about once you actually hit a snag.

---

## Summary

| Element | Minimal setup | Advanced setup |
| :--- | :--- | :--- |
| **Roles** | orchestrator + implementer | + reviewer (one-shot) |
| **Communication** | tasks.md (file) | agmsg (SQLite) |
| **Parallel work** | sequential execution | parallel via worktrees |
| **Launching Codex** | manual | watcher + approval |
| **Human's role** | PM + manual launch | PM + approval only |

The core of building a multi-agent setup for solo development is "narrowing the range of what you decide." You hand the time spent writing code to the agents and focus on design decisions, approvals, and integration.

Once this division of labor starts working, the felt speed of development changes.

---

## References

- [The Asymmetric Handoff Problem Between Claude and Codex, and How to Solve It]({% post_url 2026-06-07-multi-agent-asymmetric-handoff %}) — the design of agmsg + asymmetric handoff
- [Context Design for Keeping Agents Running Autonomously]({% post_url 2026-06-07-agent-context-management-2026 %}) — context rot and orchestrator design
- [What Is Harness Engineering?]({% post_url 2026-06-08-harness-engineering-guide %}) — the full picture of hooks, permissions, and loop design
- [agmsg — Cross-agent messaging for CLI AI agents](https://agmsg.cc/) — the official agmsg site
- [Claude Code Subagents](https://docs.anthropic.com/en/docs/claude-code/sub-agents) — Claude Code's official subagent feature
