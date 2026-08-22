---
layout: post
title: "Git Submodule vs Git Subtree: Differences and When to Use Each"
subtitle: Comparing the two ways to pull an external repository into your project
categories: Development
tags: ["Git", "Development Environment", "CLI"]
lang: en
ref: git-submodule-subtree
image:
  path: /assets/images/posts/2026-06-10-git-submodule-subtree/eyecatch.png
  alt: Paper craft contrasting a reference pointing to an external box with contents unpacked into the parent box
---

When you want to bring an external repository into your project, Git gives you two approaches: `submodule` and `subtree`. Both "pull in an external repo," but the mechanism and the day-to-day handling differ substantially.

This post lays out how each works and which situations call for which.

---

## What Is Git Submodule?

A submodule gives the parent repository a *reference* to an external repository. The actual code lives in the external repo; the parent only records "which repository, at which commit."

```
my-project/
├── .gitmodules       ← submodule configuration file
├── src/
└── libs/
    └── external-lib/ ← directory registered as a submodule
```

`.gitmodules` records the repository URL and path, and the `libs/external-lib/` directory itself is treated as a pointer to a commit hash.

### Basic Commands

```bash
# Add a submodule
git submodule add https://github.com/org/external-lib libs/external-lib

# Clone a repository including its submodules
git clone --recurse-submodules https://github.com/me/my-project

# Initialize and fetch submodules in an already-cloned repository
git submodule update --init --recursive

# Move the submodule to the latest upstream commit
git submodule update --remote
```

### Things to Watch Out For

Right after cloning a repository that contains submodules, the `libs/external-lib/` directory is empty. The code only appears once you run `git submodule update --init`. Forget this and you end up staring at "the files are missing."

The other defining trait: the parent repository controls *which commit* the submodule points at. Even as new commits pile up in the external library, the parent keeps pointing at the old one. You can call that deliberate pinning — but pulling in updates always requires an explicit operation.

---

## What Is Git Subtree?

A subtree takes the external repository's code and merges it directly into the parent repository's history. Once it's in, there is no remaining dependency on the external repo — it's just a directory.

```bash
# Add as a subtree
git subtree add --prefix=libs/external-lib \
  https://github.com/org/external-lib main --squash

# Pull in updates from the external repository
git subtree pull --prefix=libs/external-lib \
  https://github.com/org/external-lib main --squash

# Push changes back to the external repository
git subtree push --prefix=libs/external-lib \
  https://github.com/org/external-lib main
```

With `--squash`, the external repository's commit history is collapsed into a single commit before merging. If you don't want the external repo's fine-grained history in your parent repository, `--squash` is the common choice.

### Subtree's Characteristics

The big win is that people cloning the repo don't need to know anything. `git clone` alone is enough — there is no "forgot to initialize" failure mode like with submodules.

On the flip side, using it without `--squash` mixes histories and gets hard to read. And pushing modifications back upstream (`subtree push`) is somewhat involved and demands real Git knowledge.

---

## Which One to Choose

| | submodule | subtree |
| :--- | :--- | :--- |
| Coupling to the external repo | Tight (tracks per commit) | Loose (manual pull) |
| Steps after cloning | Requires `submodule update` | None |
| Burden on the team | High (everyone must understand submodules) | Low |
| Pushing changes upstream | Not hard | Somewhat complex |
| Where history lives | Stays in the external repo | Merged into the parent |

Rules of thumb:

**When submodule fits**

- You want to pin the external repo to a specific commit (library version pinning)
- You frequently push changes back to the external repo
- Everyone on the team is comfortable with Git

**When subtree fits**

- The team includes Git beginners, or your tooling doesn't handle submodules
- You use the imported code as-is and rarely update it
- You value a simple workflow

In practice, for solo projects and small teams, subtree tends to be the easier one to live with. Choose submodule when you have a concrete reason to keep tight synchronization with the external repository — that ordering causes less operational confusion.

---

## Sorting Out the Common Confusions

### "I added a submodule but the code isn't there"

You haven't run `git submodule update --init --recursive` after `git clone`. Cloning with `--recurse-submodules` avoids the problem in one step.

### "I bumped the submodule version and now the build breaks for everyone else"

After updating the submodule's commit pointer, every teammate needs to run `git submodule update`. If enforcing that is hard, document the steps in the README — or consider migrating to subtree.

### "subtree pull produced a pile of conflicts"

Switching `--squash` on or off midway invites conflicts. Pick a policy at the start and stick with it to the end.

---

## Summary

| Aspect | submodule | subtree |
| :--- | :--- | :--- |
| Mechanism | Reference to an external repo | External history merged in |
| Independence | Low (depends on the external repo) | High (independent once imported) |
| Ease of use | Takes practice | Intuitive |
| Use case | Version pinning, frequent sync | Simple import, mostly read-only |

Neither one is simply better — they serve different situations. If in doubt, start with subtree, and reach for submodule when the need for finer-grained synchronization with the external repository actually shows up. That's the practical order.
