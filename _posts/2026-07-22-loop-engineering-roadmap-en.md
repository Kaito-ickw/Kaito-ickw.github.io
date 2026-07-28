---
layout: post
title: "Loop Engineering: Moving AI Coding from Manual Prompts to Designed Loops"
subtitle: A practical reading of the 14-step roadmap from prompter to loop designer
categories: AI Development
tags: ["AI Agent", "Coding Agent", "Harness Engineering", "Context Management", "Automation", "MCP", "Design"]
lang: en
ref: loop-engineering-roadmap
image:
  path: /assets/images/posts/2026-07-22-loop-engineering-roadmap/eyecatch.png
  alt: "Risograph of a designer's hands assembling a circular work loop fitted with an inspection gate and a stop lever"
---

When you use a coding agent, much of the work still runs by hand. You write a prompt, wait for the result, read the diff, point out the problem, and run it again. Even though the AI writes the code, the role of pushing the work forward stays with the human.

"Loop engineering: the 14-step roadmap from prompter to loop designer," published by Codez (@0xCodez), lays out a way of thinking that replaces this manual operation with a system one level up. Instead of a human writing a prompt every time, you design a small system that finds work, hands it to an agent, verifies the result, saves the state, and decides the next move. That system is the loop.

The original post does not claim that everyone should immediately build autonomous loops. What matters more is first distinguishing the work that is better left without a loop. This article explains the 14 steps in three groupings: the decision to adopt, the building blocks, and operational cautions.

> The original post was published on June 17, 2026. In addition to the text on X, official material from Anthropic, OpenAI, and MCP was checked on July 22, 2026. Because product-specific features may change, this article focuses on design principles that stay useful over time.

---

## The Short Answer

Loop Engineering is not a technique for sending prompts repeatedly. It is a design that places the trigger, the execution environment, verification, state, stopping conditions, and approval outside the model.

The minimal configuration needs only these four:

1. An automation that starts on a schedule or an event
2. An instruction or skill that holds project-specific rules
3. A state file that records what is done and what comes next
4. A gate that automatically rejects bad results

You do not need to start from a large multi-agent setup. First, build a procedure that reliably succeeds once with human operation. Then record the procedure in a file, add objective verification, and only then move to scheduled runs. Skip this order, and the number of runs and the cost grow while you have no idea where it failed.

![The skeleton of an autonomous loop: trigger, fetch work, agent execution, mechanical verification, human approval, saved state and a stopping condition](/assets/images/posts/2026-07-22-loop-engineering-roadmap-en/loop-structure-en.svg){: .chart}

## Part 1: Does This Work Need a Loop?

### 1. Replace the person who writes prompts with a mechanism

In manual AI coding, a human decides the next move every time. In Loop Engineering, the part of that judgment that can be routinized is moved to an external mechanism.

For a first response to CI failures, for example, you can define a flow: "fetch the failed workflow," "classify it into an environment problem, a flaky test, or a code defect," "produce a fix only for what can be reproduced," "make the tests pass," and "hand it off as a draft PR to a human." What becomes the design target is not a single instruction to the model, but everything from discovering the work to handing it off.

This overlaps with the idea covered in [What is harness engineering]({% post_url 2026-06-08-harness-engineering-guide %}). You do not ask the model alone for performance; you place tools, permissions, records, and verification outside the model.

### 2. Check whether the four conditions are met

The original post asks you to check four conditions before building a loop.

| Condition | What to check |
| :--- | :--- |
| Repetition | Does the same kind of work occur regularly? |
| Automatic verification | Can a failure be judged by tests, type checks, lint, build, and so on? |
| Budget | Can you tolerate the cost of re-reading, exploring, failing, and retrying? |
| Execution environment | Can the agent read logs, run the code, and observe failures? |

Build a loop for a one-off investigation and you cannot recover the cost of preparing the mechanism. For work whose only success criterion is "seems good," automatic verification does not hold either. In an environment where the model can write code but not run it, all it can do is repeat guesses without seeing the failures.

This judgment is not about whether you can introduce an agent, but about whether you can make it repeat in a near-unattended state.

### 3. Separate where it works from where it does not

Good first targets include draft PRs for dependency updates, fixing lint violations, classifying CI failures, and small issues in a repository with strong tests. In all of these, the work repeats, can be judged mechanically, and is easy to revert on failure.

On the other hand, making an architecture overhaul, authentication or payments, ambiguous product decisions, or a production deploy your first loop is dangerous. The quality of judgment is hard to express with tests alone, and the impact of a wrong operation is large.

Also, when a team's bottleneck is review rather than implementation, a loop increases the number of unreviewed diffs. That the amount of generated code has grown is not the same as that the number of valuable changes has grown.

### 4. Judge an individual task in 30 seconds

Before putting a concrete task into a loop, it helps to check the following.

- It occurs regularly
- Automatic verification can reject a bad result
- The agent can run the changed code
- There is a limit on time, number of attempts, and cost
- There is human approval before merge, deploy, external sends, and the like

If even one is missing, it is better to first solidify the procedure with manual prompts. Deciding to delay when to automate is also part of loop design.

## Part 2: The Five Elements That Make Up a Loop

### 5. Automation is the loop's heartbeat

Automation starts a process on triggers such as a time, a period, or an event. OpenAI's Codex Automations also assume repetitive work such as periodic issue cleanup, summarizing CI failures, and weekly reports.

Here, it helps to think of the trigger condition and the completion condition separately. "Check every 30 minutes" is a trigger condition, and "all target tests passed" is a completion condition. With only the former, you cannot judge when it should end.

### 6. Isolate parallel work with worktrees

When multiple agents modify the same checkout at once, they may read each other's unfinished diffs and overwrite files. With a Git worktree, you can separate the working directory and branch while sharing history.

But what a worktree solves is file conflicts. It does not solve whether two changes contradict each other by design, or how many PRs a human can review. The upper limit on parallelism must be decided by review capacity, not by the number of models.

### 7. Accumulate knowledge in skills and instruction files

Explaining the same background every loop not only increases input cost but also causes rules to be left out. Put the build steps, the areas not to touch, the approaches that failed in the past, and the report format at completion into a file the agent can read every time.

What matters is not saving the full text of the conversation. It is editing it down to the knowledge needed for the next judgment. The offloading to external state explained in [Context design for keeping an agent autonomous over long runs]({% post_url 2026-06-07-agent-context-management-2026 %}) becomes, here, a reusable work procedure.

### 8. Connect to the real workplace with connectors

An agent that can only read files can produce a fix but cannot go as far as fetching issues, creating PRs, or notifying. Connect it to GitHub, an issue tracker, error monitoring, and chat through connectors such as MCP, and the loop can enter the actual work flow.

What MCP standardizes is how an AI application connects to external data and tools. It is not a mechanism that unconditionally permits the operations it connects to. You need to separate read and write permissions and keep approval for operations that affect the outside.

### 9. Separate the maker from the checker

Ask the same agent to "implement it and confirm it is correct," and it tends to affirm the approach it chose itself. So you separate the maker and the checker. Anthropic's evaluator-optimizer is also a configuration where one side generates and a separate LLM returns evaluation and feedback.

But simply placing one more verifier is not enough, because you may end up with two agents that answer "looks fine." In the end, you judge by observable results: test outcomes, type checks, the existence of expected files, the state in the database, and so on.

Anthropic's explanation of agent evals also gives an example of confirming not whether the agent said "I booked it," but whether the booking actually exists in the database as an outcome. A loop's gate can be designed with the same idea.

## Part 3: Build Small, Stop Correctly

### 10. Span sessions with a state file

In a long-running loop, do not make the conversation itself the memory device. Leave what is done, what is in progress, the next work, the reasons for failure, and open items in Markdown, JSON, an issue board, and the like.

The state file shows the current position. Place a higher-level policy separately, such as a `VISION.md` or `AGENTS.md`, and you can re-read the destination every time too. The `.planning/` in [Turning AI coding into a spec-driven process with GSD Core]({% post_url 2026-06-24-gsd-core-ai-coding-workflow %}) is also a concrete example of saving decisions and progress outside the conversation.

### 11. Grow the minimal setup from manual runs

Combine many agents, connectors, and complex schedules from the start, and isolating the cause of a failure becomes hard. The order of adoption goes like this.

1. Stabilize a single human-triggered procedure
2. Write the procedure and constraints into a skill or instruction file
3. Add a state file and an automatic gate
4. Turn it into a loop, and set a schedule last

The metrics you should measure are also not the number of runs or the amount of generated code. Look at the cost per change that passes human review, the rework rate, the review time, and the recovery time after a failure. Even if the loop produces a large number of fixes, if a human throws most of them away, the burden has not decreased.

### 12. Detect silent failures

What is troublesome in a loop is not only failures that stop with an error. There is a state where the process finishes normally and cost is incurred, but the work is not complete.

Common causes are an ambiguous completion condition, a checker that only self-evaluates, and retries with no limit. Instead of "finish when it feels good," change it to a judgeable condition such as "the specified tests pass, lint exits with code 0, and no out-of-scope files were changed."

### 13. Do not increase comprehension debt

The faster a loop runs, the faster code that no human wrote also grows. As the gap between the repository's contents and the team's understanding widens, no one can explain the whole thing during an incident. The original post calls this comprehension debt.

The countermeasures are not flashy. Keep up practices such as reading the diffs, spot-checking whether the automatic gate really catches failures, and keeping design changes that involve judgment out of scope for the loop. Automation does not eliminate review; it changes where you should review.

### 14. Manage the attack surface of unattended operation

As the time it runs unattended grows, attacks and misoperations also continue without anyone noticing. The following deserve particular attention.

- Prompt injection embedded in externally fetched skills or issue bodies
- API keys and personal information leaking into execution logs
- Write permissions added for convenience and left in place
- Merges and deploys that skip security checks and human confirmation

Give the loop least privilege, keep secrets out of the logs, and include dependency auditing and secret scanning in the gate. Review permissions periodically, not only at adoption. It is better not to leave the final authorization decision to the agent that reads external input itself.

## Where to Start in Practice

As a first subject, a weekly dependency check is easy to handle.

```text
Trigger: Every Monday
Input: Current dependencies and update candidates
Execute: Update one at a time in a worktree
Gate: install, test, lint, build
State: Record success/failure, reasons for failure, created branches
Stop: Up to 3 items or 60 minutes
Approval: Up to a draft PR. Merge is done by a human
```

In this example, the work repeats, the success conditions can be confirmed by machine, and the change is isolated in a PR. Even if it fails, it does not directly affect production. Once this is stable, you can widen the scope to classifying CI failures and small fixes.

The core of Loop Engineering is not running an agent for a long time. It is deciding in advance what to delegate, what to reject by machine, where to stop, and which operations to return to a human. Even if you move from prompts to loops, the engineer's role does not disappear. The center of gravity shifts from the work itself to designing the mechanism by which the work proceeds safely.

---

## References

- [Loop engineering: the 14-step roadmap from prompter to loop designer (X)](https://x.com/0xCodez/status/2064374643729773029)
- [Loop engineering: the 14-step roadmap from prompter to loop designer (Thread Navigator)](https://threadnavigator.com/thread/2064374643729773029/)
- [Building effective agents (Anthropic)](https://www.anthropic.com/engineering/building-effective-agents)
- [Demystifying evals for AI agents (Anthropic)](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- [Introducing the Codex app (OpenAI)](https://openai.com/index/introducing-the-codex-app/)
- [Automations (OpenAI Academy)](https://openai.com/academy/codex-automations/)
- [What is the Model Context Protocol? (Model Context Protocol)](https://modelcontextprotocol.io/docs/getting-started/intro)
```
