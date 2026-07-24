---
layout: post
title: "Cerebrating, Noodling, Clauding: Every Word Claude Code Shows While It Thinks"
subtitle: The full vocabulary of the thinking messages, sorted by category
categories: AI Development
tags: ["Claude Code", "Claude", "Coding Agent", "CLI"]
lang: en
ref: claude-code-thinking-words
---

When you use Claude Code, words like `Cogitating...` or `Noodling...` flicker by while it works. Some of them are unfamiliar even to native English speakers, and on first sight it's hard to tell what they mean.

I figured "surely there's a list in the official docs," but I couldn't find one. The vocabulary is managed as a constant inside the source code, and it has been shared with the community through posts on X (formerly Twitter) and GitHub Issues. This article collects the full list, sorted by category.

---

## Cooking and Brewing

The image is of ingredients slowly coming together. These seem to show up more often during processing that takes a while.

| Word | Meaning |
| --- | --- |
| Brewing | to brew; (of an idea) to develop over time |
| Baking | to bake |
| Marinating | to marinate; to let something soak in slowly |
| Percolating | to seep through slowly (think of a coffee maker) |
| Simmering | to cook over low heat |
| Distilling | to distill; to extract the essence |
| Cooking | to cook |
| Concocting | to concoct; to cook up (a plan) |

---

## Thought and Philosophy

The image is of deep thinking. Many of these are formal words in English that even native speakers rarely use in everyday conversation.

| Word | Meaning |
| --- | --- |
| Cogitating | to think hard, to deliberate |
| Ruminating | to ruminate; to mull something over |
| Contemplating | to contemplate |
| Pondering | to ponder carefully |
| Philosophising | to think philosophically |
| Pontificating | to pronounce judgment pompously |
| Deliberating | to deliberate; to weigh carefully |
| Musing | to muse, to be lost in thought |
| Mulling | to think something over (mulling over) |
| Meandering | to think in a wandering way |
| Interrogating | to dig into something by questioning it closely |

---

## Engineering and Assembly

The image is of designing and building a system. These tend to appear during technical work.

| Word | Meaning |
| --- | --- |
| Calculating | to calculate |
| Computing | to compute |
| Calibrating | to adjust; to calibrate |
| Orchestrating | to harmonize, like an orchestra |
| Synthesizing | to synthesize; to combine |
| Assembling | to assemble |
| Forging | to forge; to build with force |
| Wrangling | to grapple with; to wrestle into shape |
| Untangling | to untangle; to work something loose |
| Coalescing | to coalesce; to bring together into one |
| Deciphering | to decipher |
| Reticulating | to arrange in a net-like pattern |
| Crystallizing | to crystallize; to give something a clear form |
| Weaving | to weave |

---

## Humor and Fantasy

Words that are funny in meaning, or that you'd almost never come across otherwise. This is the category where Claude's playful side shows.

| Word | Meaning / Notes |
| --- | --- |
| Noodling | to think idly; also used for improvising on an instrument, as in jazz |
| Conjuring | to summon by magic |
| Scheming | to scheme; to plot (with a hint of malice) |
| Hatching | to hatch; to incubate (a plan) |
| Frolicking | to frolic; to move about lightly |
| Herding | to herd; to guide a flock |
| Honking | to honk a horn |
| Booping | to poke someone on the nose (internet slang) |
| Smooshing | to squish something soft |
| Shimmying | to shake in small movements; to move nimbly |
| Schlepping | to haul something heavy (slang, from Yiddish) |
| Discombobulating | to confuse |
| Combobulating | a coined antonym of Discombobulating (not in any dictionary) |
| Finagling | to wangle; to fiddle something into place |
| Flibbertigibbeting | to behave like a flighty, restless chatterbox (an archaic word from Middle English) |
| Puttering | to putter; to tinker or wander about |
| Moseying | to amble along leisurely |
| Clauding | "to Claude" (a proper noun turned into a verb; a complete coinage) |
| Sprinkling | to sprinkle |
| Choreographing | to choreograph; to design movement in detail |
| Waltzing | to waltz |

---

## Everyday Verbs

These look like ordinary English words, but lined up together they show a surprisingly wide range of uses.

| Word | Meaning |
| --- | --- |
| Thinking | to think |
| Processing | to process |
| Generating | to generate |
| Imagining | to imagine |
| Considering | to consider |
| Determining | to determine |
| Inferring | to infer |
| Envisioning | to envision |
| Manifesting | to manifest; to make real |
| Ideating | to generate ideas |
| Elucidating | to make clear |
| Perusing | to read closely |
| Puzzling | to puzzle over; to rack one's brain |
| Mustering | to muster; to gather or summon up |
| Actualizing | to actualize; to bring into being |
| Channelling | to channel; to focus or transmit |
| Cerebrating | to work the brain (from the verb "cerebrate") |
| Incubating | to incubate; to keep warm |
| Germinating | to germinate |
| Effecting | to effect; to bring about |
| Forming | to form |
| Doing | to do (the simplest one, which is oddly striking) |
| Accomplishing | to accomplish |
| Actioning | to action (verb use of "action"; somewhat nonstandard) |
| Churning | to churn vigorously |
| Crafting | to craft carefully |

---

## A Few Especially Interesting Words

A note on the words that stand out most across the whole list.

`Clauding` turns the proper noun into a verb — "to Claude" — something you'd almost never see in another AI tool. `Combobulating` is a coined antonym of `Discombobulating` ("to confuse") that doesn't exist in any dictionary. `Schlepping` is slang from Yiddish (the language of Eastern European Jews), a word that carries a sense of fatigue: to haul something heavy. `Flibbertigibbeting` comes from Middle English and is an archaic word meaning to behave like a flighty, restless chatterbox.

---

## What About Anthropic's Official Word?

As of the time of writing (June 2026), Anthropic's official documentation contains no list of this vocabulary.

The words are managed as a constant in the source code, and a post on X (March 2025) is widely referenced as the primary source. GitHub Issues asking to customize the displayed vocabulary (#29200, #30259) have also been filed, but nothing has been implemented yet.

According to community observations, serious topics (such as security-related processing) tend to produce plain phrases like `Setting up the calculation`, while the humorous vocabulary shows up more during lighter tasks or creative work. The vocabulary and tone appear to be varied on purpose.

---

## References

- [X: Pallav Agarwal — full list post (March 2025)](https://x.com/pallavmac/status/1897491460636778693)
- [DEV Community: The Words Claude Uses When Thinking](https://dev.to/npayyappilly/the-words-claude-uses-when-thinking-a-deep-dive-into-ais-inner-monologue-2mik)
- [GitHub Issue #29200: Allow customizing the animated thinking/status words](https://github.com/anthropics/claude-code/issues/29200)
- [GitHub Issue #30259: Customizable thinking status messages](https://github.com/anthropics/claude-code/issues/30259)
