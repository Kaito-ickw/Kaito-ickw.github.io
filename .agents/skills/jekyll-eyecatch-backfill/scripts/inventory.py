#!/usr/bin/env python3
"""Inventory idempotent eyecatch state for Japanese Jekyll posts."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
POSTS = ROOT / "_posts"
WORK = ROOT / ".eyecatch-work"


def front_matter(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    block = text.split("---\n", 2)[1]
    data: dict[str, object] = {}
    image: dict[str, str] | None = None
    for line in block.splitlines():
        if line == "image:":
            image = {}
            data["image"] = image
            continue
        if image is not None and line.startswith("  "):
            match = re.match(r"\s+(path|alt):\s*(.*)$", line)
            if match:
                image[match.group(1)] = match.group(2).strip().strip('"')
            continue
        image = None
        match = re.match(r"(title|lang|ref):\s*(.*)$", line)
        if match:
            data[match.group(1)] = match.group(2).strip().strip('"')
    return data


def candidate_numbers(work_dir: Path) -> set[int]:
    found: set[int] = set()
    candidate_dir = work_dir / "candidates"
    if not candidate_dir.is_dir():
        return found
    for path in candidate_dir.glob("candidate-*.png"):
        name = path.name
        if "-fallback" in name or "-source" in name:
            continue
        match = re.match(r"candidate-(0?[1-4])(?:-|\.)", name)
        if match:
            found.add(int(match.group(1)))
    return found


def priority(path: Path) -> tuple[int, str]:
    name = path.name
    year = int(name[:4])
    if year == 2026:
        return (0, name)
    return (1, name)


def published_image(data: dict[str, object]) -> tuple[str, bool]:
    image = data.get("image") if isinstance(data.get("image"), dict) else {}
    image_path = image.get("path", "") if isinstance(image, dict) else ""
    asset = ROOT / image_path.lstrip("/") if image_path else None
    return image_path, bool(asset and asset.exists())


def main() -> None:
    rows: list[tuple[tuple[int, str], str, Path, str, str, str]] = []
    posts = [(path, front_matter(path)) for path in sorted(POSTS.glob("*.md"))]
    by_ref: dict[str, list[tuple[Path, dict[str, object]]]] = {}
    for path, data in posts:
        ref = str(data.get("ref", ""))
        if ref:
            by_ref.setdefault(ref, []).append((path, data))

    for path, data in posts:
        if data.get("lang") != "ja":
            continue
        year = int(path.name[:4])
        if year not in {2023, 2024, 2026}:
            continue
        if "test-markdown" in path.name or "another-test" in path.name:
            continue

        slug = path.stem
        image_path, image_exists = published_image(data)
        paired = [
            pair_data
            for pair_path, pair_data in by_ref.get(str(data.get("ref", "")), [])
            if pair_path != path and pair_data.get("lang") == "en"
        ]
        pair_path, pair_exists = published_image(paired[0]) if paired else ("", False)
        work_dir = WORK / slug
        numbers = candidate_numbers(work_dir)

        if (image_exists != pair_exists and paired) or (
            image_exists and pair_exists and image_path != pair_path
        ):
            state = "pair-mismatch"
        elif image_exists:
            state = "published"
        elif image_path:
            state = "broken-published"
        elif numbers == {1, 2, 3, 4}:
            state = "selection-ready"
        elif numbers:
            state = "partial"
        else:
            state = "new"

        actionable = state != "published"
        rank = priority(path)
        if state in {"selection-ready", "partial", "broken-published", "pair-mismatch"}:
            rank = (-1, path.name)
        rows.append((rank, "yes" if actionable else "no", path, state,
                     ",".join(map(str, sorted(numbers))) or "-",
                     str(data.get("title", ""))))

    rows.sort(key=lambda row: row[0])
    print("actionable\tstate\tcandidates\tpost\ttitle")
    for _, actionable, path, state, numbers, title in rows:
        print(f"{actionable}\t{state}\t{numbers}\t{path.relative_to(ROOT)}\t{title}")


if __name__ == "__main__":
    main()
