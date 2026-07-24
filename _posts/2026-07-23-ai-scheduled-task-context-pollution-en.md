---
layout: post
title: "Why Scheduled AI Tasks Degrade the Longer You Run Them"
subtitle: How context pollution works, and how ChatGPT, Gemini, and Claude compare
categories: AI Development
tags: ["AI", "LLM", "Claude", "Claude Code"]
lang: en
ref: ai-scheduled-task-context-pollution
image:
  path: /assets/images/posts/2026-07-23-ai-scheduled-task-context-pollution/eyecatch.png
  alt: A paper collage of a closed loop that feeds its own output back into its input, with old sheets piling up as sediment below, while a single fresh sheet is shut out of the loop
---

Plenty of people use the scheduling features in ChatGPT or Claude to summarize the news every morning or to keep an eye on market movements. The first few runs come back with reasonable-looking analysis. But once you keep it running for a week, then a month, you start to notice that the output has become an oddly repetitive rephrasing of the same conclusion, or that it keeps dragging along assumptions that stopped being true long ago. You think you are giving it the same instructions, yet the quality of the answers keeps quietly slipping.

Most of the time, the cause is not the model's capability itself. It is the design decision behind the scheduled run: what exactly gets passed in as context every time.

## Why History Distorts the Analysis

The native scheduling features of chat-based AIs are often built to accumulate run results in the same chat or task. None of the vendors publish the full details of their internal implementations, but the following specifications suggest that at least some of these services do not run in a fully stateless way.

- The task is tied to a specific chat
- It remembers the content of past runs
- Results are appended to the same chat
- Additional instructions given inside the chat are saved for future runs

When past output is included in the next run's context, the model tends to treat it as an "already-settled premise" rather than a "hypothesis to be re-verified." As normal behavior for an LLM handling the continuation of a conversation, this is natural, but it fits poorly with tasks where the premises should not be fixed.

Concretely, degradation like the following can occur. It holds onto the previous hypothesis more than it should. It drags along old news or price levels. Rephrasings of past answers pile up. It self-cites its own past mistakes and thereby reinforces them. It prioritizes the recent conversation over the original task instruction. It prioritizes consistency with the past narrative over new facts.

Market analysis, news monitoring, incident and uptime monitoring, competitor research, security-information watching, daily and weekly reports — the more a task wants to evaluate the latest state from scratch every time, the worse it fits this accumulation-style execution model.

As I touched on in [Designing context to keep an agent running autonomously for a long time]({% post_url 2026-06-07-agent-context-management-2026 %}), more context is not always better. In the case of scheduled runs, what tends to pile up is not "the information this run needs" but "my own past statements," which creates a different problem from single-shot long context.

## Comparing the Services: Do They Support Fresh-Session Execution?

I checked the official documentation as of July 23, 2026. **Whether a session is fresh, and whether some separate persistent memory is in effect, are two different axes** — this is an important point shared across all three services. Below I distinguish between specifications that are officially stated and inferences drawn from them.

### ChatGPT Tasks

ChatGPT has two kinds of tasks. A "standalone" task starts a new chat each time it runs, and the result shows up in the Scheduled list. A task created inside an existing chat, on the other hand, returns to that chat and inherits the existing conversation context. You choose which mode it runs in at creation time, and the official documentation shows no setting to switch after the fact ([learn.chatgpt.com/docs/automations](https://learn.chatgpt.com/docs/automations)).

There is also a "monitoring task" type, which periodically checks for changes on the web or in connected apps, remembers the content of the previous run, and automatically stops once its termination condition is met ([help.openai.com](https://help.openai.com/en/articles/10291617-scheduled-tasks-in-chatgpt)). Given the nature of monitoring, some degree of memory is built in by design.

### Gemini Scheduled Actions

Gemini's scheduled actions are tied to a single dedicated chat — "the scheduled action chat" — and run results are appended there. If you edit the instructions inside that chat, the change is reflected in subsequent runs as well ([support.google.com/gemini/answer/16316416](https://support.google.com/gemini/answer/16316416?hl=en)). Using this feature requires Keep Activity to be on, and the documentation shows no setting to run each occurrence as an independent session. Of the three services, this is the design where history most structurally accumulates.

### Claude Cowork / Claude Code Scheduled Tasks

Claude has several mechanisms for scheduled execution.

Claude Cowork's scheduled tasks each run as an independent Cowork session, and the content of past runs is not automatically accumulated. That said, they can access saved instructions (prompts) and files stored in connected connectors and accounts ([support.claude.com](https://support.claude.com/en/articles/13854387-schedule-recurring-tasks-in-claude-cowork)).

Claude Code Desktop's scheduled tasks also start a new session on each run. But because they access local files, the state of the working folder (including uncommitted changes) carries over directly into the next run. CLAUDE.md, the allow rules in `~/.claude/settings.json`, and the contents of any SKILL.md saved per task can all have an effect. There is also a toggle to use an independent Git worktree per run; enabling it isolates the working-folder state ([code.claude.com/docs/en/desktop-scheduled-tasks](https://code.claude.com/docs/en/desktop-scheduled-tasks)).

The cloud-side Claude Code Routines start a new session each time a trigger fires, and the repository is cloned fresh from the default branch every time. Local working state does not carry over, while the CLAUDE.md and Skills committed to the repository and the configured connectors are loaded identically each time ([code.claude.com/docs/en/routines](https://code.claude.com/docs/en/routines)).

### Comparison Table

| Service | Execution unit | Handling of past runs/history | Fresh-session option | Persistent context that can have an effect |
| :--- | :--- | :--- | :--- | :--- |
| ChatGPT Tasks (standalone) | New chat | Not accumulated | Selectable at creation | Memory feature (if enabled) |
| ChatGPT Tasks (inside existing chat) | Continues existing chat | Chat history included in context every time | Not possible | Same as above |
| ChatGPT monitoring tasks | Dedicated tracking | Remembers the previous run and uses it to judge the termination condition | Unclear from official info | Memory feature (if enabled) |
| Gemini Scheduled Actions | Single dedicated chat | Results appended; instruction edits also carry to next run | Not found | Keep Activity (required) |
| Claude Cowork Scheduled Tasks | Independent session | Not accumulated | Independent by design | Connectors, saved files |
| Claude Code Desktop Scheduled Tasks | New session | The session itself is not accumulated | Independent by design | Working-folder state, CLAUDE.md, allow rules, SKILL.md (when worktree is not used) |
| Claude Code Cloud Routines | New session + fresh clone | Not accumulated | Independent by design | CLAUDE.md, Skills, and connector config committed to the repository |

## How Far Can Prompting Alone Take You?

For services that offer no fresh-session option, like Gemini, or for situations where you want to prioritize continuity, like ChatGPT's inside-an-existing-chat tasks, prompt-based mitigation becomes a realistic option.

- Instruct it to treat each run as an independent analysis
- Instruct it not to inherit past generated answers, past conclusions, or past news summaries as facts
- Instruct it to evaluate from scratch based only on the latest information fetched this run and an explicitly stated "current state"
- Instruct it, when it does reference past information, to limit that to what is needed to confirm continuity
- Instruct it not to change its judgment for the sake of consistency, even if the result differs from a past conclusion

This does not guarantee a fresh session, however. As long as the actual conversation-history data is being passed to the model, an instruction like "ignore the past" is itself just one turn within that history. There remains the possibility that the instruction gets overwritten by a newer turn, or loses its relative weight within a long history. It is safest to treat prompting as a mitigation that weakens the influence of history, not a mechanism that guarantees history is never passed in.

## The Ideal Design: Not Zero Memory, but Controlled State Management

Given all this, the goal to aim for is not "zero memory" but "controlled state management." What should be passed into each session narrows down to these five things.

1. A new session
2. Fixed analysis instructions
3. Facts such as the current configuration and monitoring targets
4. A short piece of state data summarizing only the unresolved points that should carry over from the previous run
5. The latest information fetched this run

Conversely, what you should as a rule not pass to the next run is: the full text of past daily reports, the model's past guesses, resolved discussions, old news articles, mid-conversation chatter and small talk, and the writing style and structure of past answers. There is no need to inherit the model's impressions or its stylistic quirks.

Manage state as structured data such as YAML or JSON, separate from the conversation history. For example, a task that continuously watches competitor services might look like this.

```yaml
watch_targets:
  - name: ExampleCorp
    metric: Monthly active users
    baseline: 120000
    alert_condition: Warn if down 10% or more month-over-month

standing_hypotheses:
  - Competitor A's price cut is a short-term campaign and may not continue
  - The overall market growth rate is trending toward a slowdown

open_questions:
  - Is Competitor B's new feature affecting churn rate?
  - Should the next report isolate the effect of exchange rates?

last_updated: 2026-07-22
```

Each run analyzes using only this state data and the latest information fetched this time as input. When the run finishes, it updates only the state needed for next time, not the full report text. Rather than mechanically inheriting the previous conclusions, treat `standing_hypotheses` and `open_questions` as things to be rewritten after re-evaluating each time whether they really still hold.

## External Implementation Patterns When Native Features Fall Short

When a service cannot guarantee fresh-session execution, or when you want tighter control over state management, one approach is to create a new session each time from an API or an external execution platform.

- Create a new thread or session via API every time
- Run on a schedule from GitHub Actions
- Launch a local agent via cron or similar
- Start Claude Code or Codex as a new process each time
- Save state to Markdown, YAML, JSON, SQLite, and the like

The `/fire` endpoint of Claude Code Routines is close to this idea. Once you configure an API trigger, a new session ID is issued on each request, and you can pass request-specific text (such as the alert content) in addition to the saved prompt. It is one example where the vendor's own specification provides a "fixed prompt + per-request input" structure rather than a conversation continuation ([code.claude.com/docs/en/routines](https://code.claude.com/docs/en/routines)).

The advantage of an external implementation is that it cleanly separates conversation history from persistent state. Sessions are disposable, and only the information that should carry over to the next run is explicitly saved to an external file or database. The state-file idea covered in [Turning AI coding from manual prompting into loop design]({% post_url 2026-07-22-loop-engineering-roadmap %}) applies directly as a countermeasure against history pollution in scheduled runs as well.

## Summary

What to look at when designing scheduled runs is not "whether there is memory" but "what you explicitly carry over as state, and what you throw away every time." ChatGPT, Gemini, and Claude all hold fresh-session and persistent-memory on separate axes, and which of the two weighs more differs by service. Understand the specifications of the native features, then fill the gaps with a state file and prompt design, and with an external implementation if needed. That is the realistic landing point when you want to put a task that should be evaluated from scratch every time onto a schedule.

## References

- [Scheduled tasks | ChatGPT Learn](https://learn.chatgpt.com/docs/automations)
- [Scheduled Tasks in ChatGPT | OpenAI Help Center](https://help.openai.com/en/articles/10291617-scheduled-tasks-in-chatgpt)
- [Schedule a recurring action | Gemini Apps Help](https://support.google.com/gemini/answer/16316416?hl=en)
- [Schedule recurring tasks in Claude Cowork](https://support.claude.com/en/articles/13854387-schedule-recurring-tasks-in-claude-cowork)
- [Schedule recurring tasks in Claude Code Desktop](https://code.claude.com/docs/en/desktop-scheduled-tasks)
- [Automate work with routines | Claude Code Docs](https://code.claude.com/docs/en/routines)
</content>
</invoke>
