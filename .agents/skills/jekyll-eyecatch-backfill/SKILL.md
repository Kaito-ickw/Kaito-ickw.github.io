---
name: jekyll-eyecatch-backfill
description: Add missing eyecatch images to this Jekyll blog one article at a time with an idempotent candidate-first workflow. Use when asked to process the next post without an image, resume partial eyecatch generation, present existing candidates for selection, apply a selected candidate, or backfill historical posts under _posts/ without duplicating images or front matter.
---

# Jekyll Eyecatch Backfill

Process exactly one Japanese article or Japanese-English pair per cycle. Treat the repository and `.eyecatch-work/` as the state machine; never infer completion from chat history alone.

## Load repository rules

Read these files completely before acting:

- `AGENTS.md`
- `docs/eyecatch-image-generation-workflow.md`
- the available `imagegen` skill's `SKILL.md`

Preserve unrelated dirty-worktree changes. Never edit `_config.yml` or `_site/`, and never commit.

## Inventory state

Run:

```bash
python3 .agents/skills/jekyll-eyecatch-backfill/scripts/inventory.py
```

Use its first `actionable` row. The script applies this priority:

1. unfinished candidate work for an unillustrated post;
2. 2026 Japanese posts, oldest first;
3. 2023-2024 substantive Japanese posts, oldest first;
4. test/sample and English-only posts are excluded.

Treat a Japanese-English pair as one target. If only one paired article has `image:`, synchronize the existing asset and language-specific alt instead of generating another image.

## Follow the state machine

### `published`

Skip when front matter has `image:` and the referenced file exists.

### `broken-published`

Repair a missing referenced asset only when a recoverable selected source is unambiguous. Otherwise stop and report the broken path.

### `pair-mismatch`

Reuse the existing published image for the paired article. Add an alt in the paired article's language, then build and verify.

### `selection-ready`

Do not regenerate. Report the four candidate paths, styles, dimensions, formats, and sizes. Ask the user to choose 1-4, then stop.

### `partial`

Generate only missing candidate numbers. Never overwrite an existing file; use `-v2` when a filename collision exists.

### `new`

Read the article and create `.eyecatch-work/YYYY-MM-DD-slug/brief.md` with:

- article promise;
- one visual event: objects, action, obstacle, change;
- one or two thumbnail subjects;
- generic substitutions to avoid;
- what the image communicates without text;
- candidate number, filename, and medium.

## Generate four distinct candidates

Keep the work under `.eyecatch-work/<slug>/candidates/` until selection. Do not touch post front matter or public assets.

Use four separate generations. Keep risograph as the baseline, use two appropriate standard media, and use at least one article-specific experiment. Change medium, palette, composition, and abstraction; seed variations do not count.

Preferred set:

1. risograph or screen print;
2. paper collage;
3. miniature diorama;
4. an article-specific experiment such as woodblock, blueprint, clay, architectural cutaway, or photo collage.

Use `agy` with the currently available Gemini high-quality model when the user has selected that route:

```bash
agy --model "Gemini 3.5 Flash (High)" \
  --print-timeout 30m \
  -p "<structured prompt>"
```

Do not routinely use `--dangerously-skip-permissions`. Add it only when the user or execution environment has explicitly approved automatic permission handling, and scope the prompt to one exact candidate output.

Tell agy to:

- use the actual raster image-generation tool;
- stop on quota, rate-limit, or capacity failure;
- never substitute SVG, vector art, HTML, canvas, Python drawing, or placeholders;
- save exactly one candidate file;
- edit no other file;
- perform no visual evaluation.

Every prompt must specify:

- `Use case: stylized-concept`;
- Jekyll eyecatch and Home thumbnail as the asset;
- the article promise and concrete visual event;
- a candidate-specific medium, palette, and composition;
- exactly 1200x675 PNG, 16:9 full-bleed landscape with the subject in the central safe area;
- readability around 320x180;
- no text, letters, numbers, logos, watermark, fake UI, or code;
- no generic glowing network, robot portrait, dark navy-neon technology scene, multi-explanation infographic, or framed poster inside the canvas.

If quota, rate-limit, or capacity fails:

1. stop immediately without switching model or service;
2. report generated and missing candidate numbers;
3. inspect the latest agy log for `reason`, `quotaResetDelay`, and `quotaResetTimeStamp`;
4. convert the timestamp to JST and report it;
5. ask for feedback on any generated candidates before waiting for recovery.

## Verify without viewing

Do not open, screenshot, compare, thumbnail, or visually judge generated candidates. Use `file`, `ffprobe`, and `du` only.

Exclude these from the four valid candidates:

- `*-fallback.*` and `*-source.*`;
- anything under `archive/`;
- comparison sheets;
- SVG, HTML, code-drawn images, and placeholders.

Aim to save every candidate as a final-ready 1200x675 PNG. If a generated image has the same 16:9 ratio and is larger, downscale it without cropping before selection. Never upscale. Do not crop a non-16:9 image before selection unless the user explicitly permits it.

When four valid candidates exist, present their paths, styles, dimensions, formats, and sizes. Ask the user:

1. which candidate or one to two directions to keep;
2. which best represents the article;
3. which elements to preserve or change;
4. whether to adopt now or iterate.

If iterating, change only one of story, medium, palette, composition, or subject scale at a time. Do not regenerate all four unless the user requests a new exploration. Never crop before selection without explicit permission.

## Apply a selected candidate

Only after the user chooses a candidate:

1. Create `assets/images/posts/YYYY-MM-DD-slug/eyecatch.png` from the selected direction.
2. Use the existing 1200x675 candidate as-is. If normalization remains necessary, downscale without cropping when possible; center-crop only after selection or explicit permission. Never upscale a smaller source; regenerate it.
3. Add `image.path` and descriptive alt to the Japanese post.
4. If paired, reuse the same image and write an English alt for the English post.
5. Never use `banner:`.
6. If the PNG exceeds 2 MB, report the size; do not convert or apply lossy compression without permission.

## Validate publication

Run:

```bash
git diff --check
git status --short --ignored .eyecatch-work _posts assets/images/posts
docker compose run --rm jekyll bundle exec jekyll build
```

Confirm that `.eyecatch-work/` remains ignored and that selection-stage work did not modify tracked posts or public assets.

Inspect generated HTML for:

- article-header image path and alt;
- Japanese Home thumbnail;
- English Home thumbnail when paired;
- `og:image` and `og:image:alt`;
- `twitter:image` and `twitter:image:alt`.

Report the adopted asset path, dimensions, size, updated posts, verified surfaces, build result, diff-check result, next target, and a commit-message suggestion. Do not commit.
