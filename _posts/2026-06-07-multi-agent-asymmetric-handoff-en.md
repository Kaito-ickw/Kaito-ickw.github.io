---
layout: post
title: "The Asymmetric Handoff Problem Between Claude and Codex"
subtitle: Designing message transport, process wake-up, and execution policy as three separate layers
categories: AI Development
tags: ["Claude Code", "Codex", "agmsg", "Coding Agent", "AI-Native Development"]
lang: en
ref: multi-agent-asymmetric-handoff
image:
  path: /assets/images/posts/2026-06-07-multi-agent-asymmetric-handoff/eyecatch.png
  alt: Messages and work being handed off between multiple computers
---

Combine several AI agents to drive development and you run into an asymmetric problem.

One direction works fine. Codex finishes an implementation and sends a message, and a waiting Claude detects it and starts the review. The reverse direction does not behave the same way. Claude reviews, sends a fix request back to Codex, but Codex has already stopped and won't come pick the message up on its own.

This article works through the cause of that asymmetry and compares six patterns for resolving it.

---

## The Current Multi-Agent Setup

Here is the setup we're assuming.

```
Claude Code  ── orchestrator / architect
             ── design, task breakdown, review, integration into main
             ── agmsg identity: team=ailedger / name=architect
             ── waits for messages in monitor mode

Codex        ── backend implementer
             ── continuous implementation of API, DB, and tests
             ── agmsg identity: team=ailedger / name=backend
             ── agmsg delivery mode is turn or off

agy/Gemini   ── one-shot machine review (not resident)
```

**agmsg** is an inter-agent messaging layer built on SQLite. It uses a shared SQLite database inside the same devcontainer, requiring no network and no resident daemon. The message format looks like this.

```text
START   <task-id> <description>
DONE    <task-id> -> <recipient> <content>
CHANGES <task-id> -> backend <feedback>
APPROVED <task-id> -> orchestrator ready to merge
BLOCKED <task-id> by <reason>
LOWQUOTA <name> <rough remaining>
```

Git work happens in a dedicated worktree/branch per agent. The architect issues a task, Codex implements it and sends `DONE`. Claude reviews and either merges or returns `CHANGES`.

---

## The One-Way Flow That Works

Right now, the following flow works without trouble.

```text
Codex finishes an implementation
  → agmsg: DONE task-001 -> architect implementation complete
  → Claude, in monitor mode, detects it
  → Claude: checks the diff with git diff
  → Claude: reviews and tests
  → merge, or send CHANGES
```

Claude waits in `monitor` mode, so when something new lands in its agmsg inbox it can start processing automatically. That is why the one-way flow works.

---

## Why Claude → Codex Stalls

The reverse flow gets stuck.

```text
Claude finishes a review
  → agmsg: CHANGES task-001 -> backend please fix XYZ
  → Codex has stopped after its previous turn ended
  → a stopped Codex can't watch its own inbox
  → no new Codex turn starts
  → the message just sits in the inbox
```

A natural question follows: "Why can't Codex pick the message up itself?" The next section works through the reason.

---

## The Difference Between `turn` Mode and `monitor` Mode

Claude's `monitor` mode continuously watches the agmsg inbox and starts processing when a new message arrives.

Codex's `turn` mode **is different**. What `turn` mode provides is this:

- At the end of an active Codex turn, a stop hook checks the inbox
- If there is a message at that moment, it can be handled within the same turn

What `turn` mode does **not** provide is this:

- Continuous monitoring after a turn ends
- A daemon that waits for new messages
- A way to start a stopped Codex process from outside
- A mechanism for Claude to directly begin a new Codex turn

Once a Codex turn ends, its execution context is gone. Even if a message lands in agmsg, there is no process to receive it.

---

## Transport and Process Wake-Up Are Separate Problems

This is the core of the design. The problem needs to be split into three layers.

```
Layer 1: Message transport
  → agmsg delivers the message
  → this layer currently works

Layer 2: Wake-up mechanism
  → start a stopped Codex process
  → this layer is currently missing

Layer 3: Execution policy
  → once started, decide what may run and with what permissions
  → full automation always requires this to be designed
```

**agmsg mainly solves Layer 1.**  
**What's missing here is Layer 2.**  
If you're aiming for full automation, **Layer 3 has to be designed too.**

Try to implement while conflating these three layers, and you get the misconception that "sending a message through agmsg should make Codex move," which leaves unexpected gaps.

---

## Six Patterns for Resolving It

### Pattern 1: Human-Initiated Wake-Up

A human checks Claude's CHANGES/TASK notification and manually restarts Codex.

```text
Claude → agmsg CHANGES
  → human checks the inbox (periodic manual check)
  → human starts Codex
  → Codex implements and fixes
```

**Assessment:**

| Aspect | Rating |
| :--- | :--- |
| Automation level | Lowest (waits on a human) |
| Implementation cost | Near zero |
| Misfire risk | Lowest |
| Double-start risk | Low, since a human manages it |
| Overnight / away | Stalls |
| Fit for small personal projects | **High** |

At a scale where full automation isn't needed, this is the simplest and safest option. It's worth not overweighting "we haven't automated it" as a downside. A workflow where you wake up, check the inbox, and then start the agent has a real upside: it prevents unexpected runaway behavior.

---

### Pattern 2: Time-Bounded Polling by Codex

Don't let the Codex turn end; keep checking the inbox at a fixed interval.

```bash
# run within a Codex turn
MAX_WAIT=1800  # 30 minutes
INTERVAL=300   # 5 minutes
elapsed=0

while [ $elapsed -lt $MAX_WAIT ]; do
  msg="$(agmsg inbox --name backend --team ailedger 2>/dev/null)"
  if echo "$msg" | grep -qE '^(CHANGES|TASK|APPROVED)'; then
    echo "message received: $msg"
    break
  fi
  sleep $INTERVAL
  elapsed=$((elapsed + INTERVAL))
done
```

**Assessment:**

| Aspect | Rating |
| :--- | :--- |
| Automation level | Medium (self-contained within a turn) |
| Implementation cost | Low |
| Extra infrastructure | None |
| Turn occupancy | **Yes** (keeps using the turn) |
| Resilience to session disconnect | Weak (a disconnect fails it) |
| Long waits | Poor fit (cost and risk grow) |

Whether "the model bills while sleeping" depends on your execution environment and provider. Since it can't be stated definitively, verify it in your own environment if you plan long polling.

For short review waits (within 10–15 minutes) it works with no extra infrastructure. Because it keeps the turn occupied, though, you have to plan its use around concurrent tasks.

---

### Pattern 3: A Model-Independent Lightweight Watcher

A bash script running outside the model watches agmsg and notifies a human.

```bash
#!/usr/bin/env bash
# watcher.sh ── watch the agmsg inbox and notify (does not start Codex)

TEAM="ailedger"
NAME="backend"
INTERVAL=30

while true; do
  msg="$(agmsg inbox --name "$NAME" --team "$TEAM" 2>/dev/null)"
  if [ -n "$msg" ]; then
    task_id="$(echo "$msg" | awk '{print $2}')"
    echo "[watcher] new: $msg"
    echo "[watcher] to start Codex:"
    echo "  codex --task-id $task_id"
    # add OS/Slack notifications as needed
    # notify-send "agmsg new" "$msg" 2>/dev/null
  fi
  sleep $INTERVAL
done
```

This watcher **does not start Codex itself**. It stops at notifying the human and showing the start command.

**Assessment:**

| Aspect | Rating |
| :--- | :--- |
| Automation level | Semi-auto (notification only) |
| Implementation cost | Low |
| Model wait cost | None |
| Resilience to session disconnect | Strong (the shell keeps running) |
| Fit with agmsg | Good (uses only the provided CLI) |
| Safety | High (a human starts Codex) |

One important constraint: **never read or write the SQLite that agmsg manages directly**. Use only the provided CLI scripts to preserve agmsg's integrity.

Because the addition to the current setup is minimal, no model cost is incurred, and a human does the final check, **this is the most realistic first solution to adopt**.

---

### Pattern 4: Automatic Codex Wake-Up via a Dispatcher

An external dispatcher detects a new TASK/CHANGES and starts Codex CLI as a one-shot.

```text
Claude → agmsg TASK/CHANGES
  → dispatcher checks the inbox every 30 seconds
  → extracts task-id and validates against an allowlist
  → acquires a per-task-id lock
  → confirms the target worktree exists
  → starts Codex CLI as a one-shot
  → Codex implements and verifies
  → agmsg DONE / BLOCKED
  → releases the lock and records a log
  → process exits
```

Pseudo-code showing the safety requirements.

```bash
#!/usr/bin/env bash
# dispatcher.sh (pseudo-code ── complete the safety design before production use)

ALLOWED_REPOS=("/workspace")
ALLOWED_SENDERS=("architect")
LOCK_DIR="/tmp/agmsg-locks"
MAX_RETRY=3
MAX_RUNTIME=3600  # 60 minutes

mkdir -p "$LOCK_DIR"

while true; do
  msg="$(agmsg inbox --name backend --team ailedger 2>/dev/null)"

  if [ -z "$msg" ]; then
    sleep 30
    continue
  fi

  # validate message type (only TASK / CHANGES)
  msg_type="$(echo "$msg" | awk '{print $1}')"
  if ! echo "$msg_type" | grep -qE '^(TASK|CHANGES)$'; then
    sleep 30
    continue
  fi

  # validate sender (only architect allowed)
  sender="$(echo "$msg" | grep -oP 'from=\K\S+')"
  if [ "$sender" != "architect" ]; then
    echo "[dispatcher] invalid sender: $sender"
    sleep 30
    continue
  fi

  # extract and validate task-id (alphanumerics and hyphens only)
  task_id="$(echo "$msg" | awk '{print $2}' | grep -E '^[a-zA-Z0-9-]+$')"
  if [ -z "$task_id" ]; then
    echo "[dispatcher] task-id validation failed"
    sleep 30
    continue
  fi

  # prevent double-start (task-id lock)
  lock_file="$LOCK_DIR/$task_id.lock"
  if [ -f "$lock_file" ]; then
    echo "[dispatcher] $task_id is already running"
    sleep 30
    continue
  fi

  # check LOWQUOTA
  quota="$(agmsg inbox --name backend --team ailedger --type LOWQUOTA 2>/dev/null)"
  if [ -n "$quota" ]; then
    echo "[dispatcher] stopping due to low quota: $quota"
    break
  fi

  # validate worktree against allowlist
  worktree="$(echo "$msg" | grep -oP 'worktree=\K\S+')"
  valid_repo=false
  for allowed in "${ALLOWED_REPOS[@]}"; do
    if [[ "$worktree" == "$allowed"* ]]; then
      valid_repo=true
      break
    fi
  done
  if [ "$valid_repo" = false ]; then
    echo "[dispatcher] worktree not allowed: $worktree"
    agmsg send --name architect --team ailedger "BLOCKED $task_id by worktree not allowed"
    sleep 30
    continue
  fi

  # acquire lock → start → release
  touch "$lock_file"
  echo "[dispatcher] starting $task_id (worktree: $worktree)"

  # never pass the message body straight to the shell
  # no eval, no string expansion
  timeout "$MAX_RUNTIME" codex \
    --worktree "$worktree" \
    --task-id "$task_id" \
    --no-auto-approve-destructive \
    2>&1 | tee "/tmp/agmsg-logs/$task_id.log"

  exit_code=$?
  rm -f "$lock_file"

  if [ $exit_code -ne 0 ]; then
    agmsg send --name architect --team ailedger \
      "BLOCKED $task_id by Codex abnormal exit (exit=$exit_code)"
  fi

  sleep 30
done
```

**Mandatory safety requirements (implement all of them if you build a dispatcher):**

- Prevent double-starting the same task-id (file lock, etc.)
- Prevent parallel starts of the same Codex provider
- Force-terminate at a maximum runtime
- Cap the maximum retry count
- Target only allowed worktrees
- Accept only allowed senders (architect only)
- Don't start on anything other than `TASK` and `CHANGES`
- Don't `eval` the message body or run it directly as a shell command
- Validate task-id/branch/worktree against an allowlist
- Don't auto-approve destructive commands
- Stop on receiving LOWQUOTA
- Correlate logs with task-id
- Return `BLOCKED` on abnormal exit
- Detect and prevent loops
- A kill switch a human can use to stop it (PID file, or a signal)

**Assessment:**

| Aspect | Rating |
| :--- | :--- |
| Automation level | High |
| Implementation cost | **High** (many safety requirements) |
| Misfire risk | Reducible depending on design |
| Double-start risk | Prevented with locks |
| Security | Design matters |
| Auditability | Logs required |

---

### Pattern 5: Keeping the Codex Session Alive with tmux or Similar

Keep the Codex session alive with a terminal multiplexer like tmux, and have an external watcher inject keystrokes.

```bash
# conceptual example (not for production use)
tmux send-keys -t codex-session "checking agmsg inbox..." Enter
```

**Assessment:**

| Aspect | Rating |
| :--- | :--- |
| Conversation context retention | Possible but unstable |
| Reliability of input injection | **Low** (depends on the CLI UI) |
| Dependence on session state | Strong |
| Safety for unattended operation | Serious concerns |
| Sensitivity to CLI UI changes | Easily affected |

Injecting keys with tmux won't work correctly unless you can precisely track the CLI's prompt state. A single change to the Codex CLI UI can break the script. It's useful for thinking about structure as an early idea for full automation, but there's little reason to adopt it for production.

---

### Pattern 6: Using GitHub / CI as a Job Queue

Trigger Codex on a runner from GitHub Issues, PR comments, labels, `workflow_dispatch`, and the like.

```yaml
# .github/workflows/codex-dispatch.yml
on:
  workflow_dispatch:
    inputs:
      task_id:
        description: 'task-id'
        required: true
jobs:
  run-codex:
    runs-on: self-hosted
    steps:
      - name: Run Codex for task
        run: codex --task-id ${{ github.event.inputs.task_id }}
```

**Assessment:**

| Aspect | Rating |
| :--- | :--- |
| Audit log | **Rich** (kept in GitHub history) |
| Triggering from outside the repo | Possible |
| Required infrastructure | GitHub Actions runner (self-hosted or GitHub hosted) |
| Secret management | Manageable via GitHub Secrets |
| Fit with the current local-first policy | Low |
| Risk of dual sources of truth with agmsg | **Present** (state management gets distributed) |

The current setup prioritizes local-first and low cost, and we'd rather avoid a dual source of truth between agmsg and GitHub state. It's a strong option once you need a large team or triggers from outside, but for the early phase of personal or small-team development the setup cost often doesn't pay off.

---

## Comparison Table

| Approach | Automation | Impl. cost | Model wait cost | Misfire risk | Double-start risk | Disconnect resilience | Auditability | agmsg fit | Small-scale fit |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1. Human-initiated wake-up | ✗ | Minimal | None | Lowest | Lowest | Strong | Low | ◎ | **◎** |
| 2. Codex polling | △ | Low | Yes | Low | Low | Weak | Low | ◎ | △ |
| 3. Lightweight watcher | △ | Low | None | Low | Low | Strong | Medium | ◎ | **○** |
| 4. Dispatcher auto-start | ◎ | **High** | None | Depends on design | Reduced with locks | Strong | High | ○ | △ |
| 5. tmux session retention | ○ | Medium | Yes | Medium | Medium | Weak | Low | △ | ✗ |
| 6. GitHub/CI | ◎ | High | None | Low | Low | Strong | **High** | △ | ✗ |

---

## A Recommended Phased Rollout

Don't aim for full automation from the start. Widen the scope of automation in stages, while minimizing the damage from misfires, double-starts, and runaway behavior.

### Phase A: Semi-Automatic Notification (deployable now)

A lightweight watcher detects TASK/CHANGES and notifies a human. A human starts Codex.

```bash
# watcher.sh (minimal)
while true; do
  msg="$(agmsg inbox --name backend --team ailedger 2>/dev/null)"
  [ -n "$msg" ] && echo "[$(date)] new: $msg"
  sleep 30
done
```

What you get at this stage:

- You immediately know a message is stuck even while Codex is stopped
- No model cost
- The decision to start is always with a human

### Phase B: Approval-Gated Wake-Up

The watcher shows the start candidate, and one human approval starts Codex as a one-shot.

```bash
# start with an approval prompt
read -p "Start Codex? [y/N] " confirm
if [ "$confirm" = "y" ]; then
  touch "$LOCK_DIR/$task_id.lock"
  timeout 3600 codex --task-id "$task_id" --worktree "$worktree"
  rm -f "$LOCK_DIR/$task_id.lock"
fi
```

What you add at this stage:

- task-id lock (prevents double-start)
- Timeout (maximum runtime)
- Log recording (correlated to task-id)

### Phase C: Constrained Auto-Start

Automate only for stable use cases.

Conditions:

- Only messages from the architect
- Start only in allowed worktrees
- One process per task (lock required)
- Cap the number of fixes (prevents infinite loops)
- Automatically return messages that need design judgment as `BLOCKED`

**Why not adopt full automation from the start:**

At the moment, some of the specifics of the Codex CLI's interface and behavior aren't settled enough for the specs that automated judgment requires. And if the dispatcher mistakenly starts Codex repeatedly for the same task, competing commits to the same worktree can occur. A phased rollout lets you detect problems early at each phase and proceed safely.

---

## Safety Requirements When Designing a Dispatcher

For a dispatcher to become something you can actually use, just processing free-form messages as-is is not enough.

**The danger of driving a dispatcher on free text alone:**

```text
# if the dispatcher processes this agmsg message straight in the shell...
CHANGES task-001 -> backend ; rm -rf /workspace

# expanded via eval or $(), an unintended command runs
```

For this reason, consider moving to a structured message format.

```json
{
  "type": "TASK",
  "task_id": "MIG-001",
  "from": "architect",
  "to": "backend",
  "repo": "/workspace",
  "worktree": "/workspace/.worktrees/alembic",
  "branch": "feat/alembic",
  "action": "implement",
  "max_runtime_minutes": 60,
  "requires_human_approval": true
}
```

That said, the current agmsg is designed around free text. As a migration that doesn't break compatibility, there's the option of prefixing existing messages with `TASKJSON`.

```text
# normal free text (the existing format ── unchanged)
TASK task-002 -> backend implement DB migration

# structured message for the dispatcher (new format)
TASKJSON {"type":"TASK","task_id":"MIG-001","from":"architect",...}
```

With this approach:

- Existing free-text messages keep working
- The dispatcher parses only the ones with the `TASKJSON` prefix
- The dispatcher does not act on free-text `TASK` (safe)
- You can advance structured support in stages

---

## A Recommended Setup for This Project

For the current development of an "AI-native ledger system," the recommendation is as follows.

**Do now:**

1. **Don't make Codex sleep for long stretches**  
   Keep in-turn polling short (within 10–15 minutes)

2. **Introduce a model-independent lightweight watcher** (Phase A)  
   Monitor using only the agmsg CLI and notify a human  
   Don't read SQLite directly — use only the agmsg CLI

3. **Operate with human approval at first**  
   Watcher notifies → human checks → manually starts Codex  
   Use this to concretely understand "in which situations do I want to start Codex"

**Once stable, proceed with:**

4. **Introduce per-task-id double-start prevention** (Phase B)  
   Simple to implement with a lock file

5. **Move to constrained one-shot auto-start** (Phase C)  
   Target only structured messages in the `TASKJSON` format  
   After you've assembled worktree allowlist, sender validation, timeout, and LOWQUOTA stop

**Keep doing continuously:**

6. **Don't run two resident Codex instances in parallel**  
   Starting two instances of the same provider doubles rate consumption

7. **Don't auto-process design judgments — return them to the architect**  
   Use `BLOCKED` to defer to human judgment  
   It's cheaper than "Codex keeps implementing while unsure"

---

## Summary

The asymmetric handoff problem in multi-agent development becomes tractable once you recognize that "the mechanism that delivers a message" and "the mechanism that starts a stopped process" are different things.

agmsg handles Layer 1 (message transport), but Layer 2 (process wake-up) and Layer 3 (execution policy) need to be designed separately.

Full automation is a valid end goal, but without a phased rollout you create the risk that "Codex keeps repeating unintended implementations while no one is watching."

First build a state where a human can see what's going on with a lightweight watcher, then add approval flow, locks, and timeouts, and only move to auto-start once you've confirmed things work. This order is, I think, the reasonable one for small personal development.

---

## Appendix: Notes on Using agmsg

- **Never read or write** the SQLite that agmsg manages directly
- Use only the provided CLI scripts
- Don't `eval` the message body
- Don't run it directly as a shell string
- Validate task-id / branch / worktree against an allowlist
- If you build a dispatcher, get a feel for real operation with Phase A and B first

---

## References

### agmsg

- [agmsg — Cross-agent messaging for CLI AI agents](https://agmsg.cc/) — official site. Install steps, mode list, quick start
- [GitHub: fujibee/agmsg](https://github.com/fujibee/agmsg) — source code, setup scripts, issue tracker
- [I built agmsg so Claude Code and Codex could stop using me as a copy-paste relay](https://dev.to/fujibee/i-built-agmsg-so-claude-code-and-codex-could-stop-using-me-as-a-copy-paste-relay-m42) — the author's DEV Community write-up. Detailed on the design background and use cases

### Claude Code

- [Hooks reference — Claude Code Docs](https://docs.anthropic.com/en/docs/claude-code/hooks) — event specs and configuration for Stop / SessionStart / PostToolUse and other hooks

### Codex CLI

- [Codex CLI — OpenAI Developers](https://developers.openai.com/codex/cli) — Codex CLI overview and install
- [Features — Codex CLI](https://developers.openai.com/codex/cli/features) — feature list for hooks and agent mode
- [Command line options — Codex CLI](https://developers.openai.com/codex/cli/reference) — CLI options reference
