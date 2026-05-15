# Specification & Prompt: Tech Brand Ecosystem (X & Blog)

## 1. Context & Objective
This document outlines the strategic integration and visual/content alignment between my X (Twitter) account and my Jekyll-based technical blog (`waka-ds.com`). 
The goal is to shift the brand positioning from a "learner's journal" (独学) to **"The Practical Architect"**—a professional platform highlighting expertise in IT consulting, data engineering, AI agents, and SaaS optimization.

## 2. Language Strategy: Hybrid Model
*   **Target Audience:** Forward-thinking tech professionals, PMs, and recruiters in Japan who value global technical standards and AI/SaaS insights.
*   **Base Language:** Japanese (for deep explanations, insights, and structural commentary).
*   **English Usage (Active Tool):** Technical terms, UI components, code comments, and skill summaries (Resume style) will remain in their native English form. No over-simplification of technical concepts.

---

## 3. Platform Roles & Data Flow
The ecosystem operates on a **"Hub and Spoke"** model, dividing information into **Flow** (real-time/engagement) and **Stock** (structured/authoritative).


```

[ X (Twitter) ] ───(High Reaction / Validation)───> [ Jekyll Blog (waka-ds.com) ]
(Flow & Experiments)                                 (Stock & Portfolio)

* Raw architecture ideas                             - Production-ready deep dives
* WIP AI Agent snippets                              - Comprehensive Docker/WSL2 guides
* Tech & Market insights                             - "About Me" as a professional bio

```

---

## 4. Brand Identity & Visual Specs

### 4.1 Design Concept
*   **Concept Name:** The Practical Architect / The IT Blueprint
*   **Tone & Manner:** Analytical, utility-first, professional, global-ready.
*   **Key Colors:** Teal (Primary Accent) & Navy Blue (Base/Trust)

### 4.2 X Account Assets
*   **Display Name:** `Waka / Data & AI Architect` (Include "Data & AI Architect" for clarity and SEO)
*   **Handle (@):** `@waka_ds_tech`
*   **Bio (Hybrid):** 
    > IT Consultant | Architect at Waka-DS.com. Building AI agents & data pipelines. Actionable insights on tech, finance, and career leverage. Translating complexity into growth. #IT #AI #Data #SaaS #Career #JP 🇯🇵

### 4.3 Jekyll Blog (waka-ds.com) Alignment
*   **Site Title:** `Waka-DS.com` (Capitalize 'Waka' and 'DS' for readability)
*   **Subtitle/Tagline:** `System Architecture & Data Strategy`
*   **UI Elements:** Use clean, minimalist English for system navigation (e.g., `Posts`, `About`, `Tags`).

---

## 5. Execution Tasks (Instructions for AI / Claude Code)

You are tasked with helping me implement this ecosystem. Please execute the following steps within this Jekyll project. Ensure that `.claude` is included in the Jekyll build process if necessary via `_config.yml`.

### Task 1: UI Typography & Palette Configuration
*   Inspect the project's CSS/SCSS or Tailwind configuration.
*   Introduce a clean, modern sans-serif font stack (e.g., combining `Inter` for alphanumerics and a clean Gothic font for Japanese) to ensure code blocks and mixed-language prose look highly professional.
*   Apply the **Teal/Navy** accent color profile to links, headers, and highlights.

### Task 2: Hybrid "About Me" (about.md) Generation
*   Rewrite the primary profile page (`about.md` or equivalent layout).
*   **Structure Requirement:**
    *   **Introduction:** High-level professional summary in natural, sharp Japanese as an IT Consultant.
    *   **Core Competencies / Projects:** Bulleted lists using English frameworks (e.g., *Data Engineering & Automation*, *Infrastructure as Code*), detailing hands-on work with Docker, WSL2, Python, TypeScript, and AI agent implementations.
    *   **Tone:** Completely eliminate beginner-oriented phrases like "勉強中です". Position everything around building, evaluating, and deploying solutions.

### Task 3: Content Pipeline Automation Script
*   Draft a local Python helper script (e.g., `_scripts/tweet_summarizer.py`) that parses a Jekyll Markdown post, extracts key code snippets and bullet points, and generates a structured draft for an X thread within character limits.

---

## 6. Constraints & Preferences
*   Maintain Jekyll front-matter formatting strictly when editing files.
*   Do not break existing liquid templates; strictly enhance styling and markdown content.

```
