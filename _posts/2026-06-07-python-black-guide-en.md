---
layout: post
title: "What Is Black for Python? — Automating Code Formatting in AI-Native Development"
subtitle: A practical introduction to formatters, configuration, VS Code, and CI
categories: Development
tags: ["Python", "Black", "Code Formatter", "AI-Native Development", "Development Environment"]
lang: en
ref: python-black-guide
---

When AI writes Python code, style differences can easily appear within the same project:

- Single and double quotes become mixed
- Function arguments are packed onto one line
- Line breaks and whitespace differ from file to file
- Unrelated formatting changes appear whenever a human or AI edits the code

Because the code still runs, these issues are easy to postpone. As the number of changes grows, however, code reviews become harder to read and actual logic changes get buried in formatting noise.

**Black** automatically standardizes this "visual appearance" of code.

---

## The Short Answer

Black is a **code formatter** that automatically rewrites Python code into a consistent style.

```bash
black .
```

In most cases, this one command formats every Python file in the project.

Black's role can be summarized in one sentence:

> Stop making humans and AI decide how code should look, and give the entire project one consistent style.

Black does not find bugs or make code faster. It is a tool for **standardizing notation without changing the logic**.

---

## What Does Black Do?

Python allows the same behavior to be expressed in many visual styles.

For example, the following code runs, but inconsistent whitespace and line breaks make it difficult to read.

### Before Running Black

```python
from typing import  Any,Dict

def build_prompt(user_name:str,logs:list[dict[str,Any]],model: str='gpt-4.1',max_output_tokens:int=1000):
  messages=[{'role':'system','content':'You are a log analyst.'},{'role':'user','content':f'Analyze logs for {user_name}: {logs}'}]
  return {'model':model,'messages':messages,'max_output_tokens':max_output_tokens}
```

Run Black on the file:

```bash
black app.py
```

### After Running Black

```python
from typing import Any, Dict


def build_prompt(
    user_name: str,
    logs: list[dict[str, Any]],
    model: str = "gpt-4.1",
    max_output_tokens: int = 1000,
):
    messages = [
        {"role": "system", "content": "You are a log analyst."},
        {
            "role": "user",
            "content": f"Analyze logs for {user_name}: {logs}",
        },
    ]
    return {
        "model": model,
        "messages": messages,
        "max_output_tokens": max_output_tokens,
    }
```

The behavior is unchanged, but Black automatically:

- Adds spaces around operators and type annotations
- Splits long lines across multiple lines
- Standardizes indentation
- Uses double quotes for strings by default
- Adds trailing commas to multiline arguments and elements
- Inserts the required blank lines between functions

There is no need to fix each item manually. Running Black repeatedly produces the same format from the same input.

---

## Formatters vs Linters

The most important distinction when learning Black is the difference between a **formatter and a linter**.

| Tool Type | Examples | Primary Role |
| :--- | :--- | :--- |
| Formatter | Black | Automatically format whitespace, line breaks, quotes, and similar details |
| Linter | Ruff, Flake8 | Detect unused variables, risky patterns, and other static issues |
| Type checker | mypy, Pyright | Detect type inconsistencies |
| Test runner | pytest | Verify that behavior matches expectations |

For example, Black will not fix the logical bug in this code:

```python
def calculate_average(total: float, count: int) -> float:
    return total / count
```

If `count` is `0`, the function raises `ZeroDivisionError`. That is not a formatting problem, so it is outside Black's scope.

Introducing Black does not remove the need for linting, type checking, or tests.

```bash
black .
ruff check .
mypy .
pytest
```

Each command examines the code from a different angle, so they are most effective when used together.

> `ruff format` performs the same formatter role as Black. A project that uses Black does not need to run both formatters. In contrast, `ruff check` is a linter and can be used alongside Black.

---

## Why Does Black Have So Few Settings?

Black is described as an **opinionated formatter**.

Many tools allow teams to configure indentation, quotes, line breaks, and other details. More configuration, however, brings back the debate over which style to choose.

Black deliberately limits customization and makes most formatting decisions itself.

```text
Which line break is easier to read?
Should we use single or double quotes?
Should multiline arguments have trailing commas?
```

Black's philosophy is to stop spending time on these discussions and use that time to review logic and design instead.

### The Default Line Length Is 88 Characters

By default, Black formats code around a line length of **88 characters**.

This is slightly longer than the well-known 79-character recommendation in PEP 8. It balances avoiding unnecessarily tall code with keeping lines from becoming too wide.

The 88-character value is not an absolute limit. Black may leave longer lines when strings or expressions cannot be split.

---

## Installation and Basic Usage

As of June 2026, Black requires Python 3.10 or later in the environment where Black itself runs.

### With pip

```bash
python -m pip install black
```

### With uv

```bash
uv add --dev black
```

Adding Black as a development dependency makes it easier for the team and CI to use the same version.

### Format One File

```bash
black app.py
```

### Format a Directory

```bash
black src tests
```

### Format the Entire Project

```bash
black .
```

If the `black` command is not available in the current environment, run it as a module:

```bash
python -m black .
```

---

## Check Changes Without Rewriting Files

Black normally rewrites files in place. Use `--diff` to preview the changes first.

```bash
black --diff .
```

Use `--check` in CI or anywhere you only need to determine whether formatting is required.

```bash
black --check .
```

| Command | Rewrites Files | Use |
| :--- | :---: | :--- |
| `black .` | Yes | Format code locally |
| `black --diff .` | No | Preview the proposed changes |
| `black --check .` | No | Check whether files are already formatted |
| `black --check --diff .` | No | Check in CI and also print the diff |

`--check` returns exit code `1` when it finds files that need formatting, which makes it directly usable as a CI check.

---

## Share Configuration Through pyproject.toml

Black's settings belong in `pyproject.toml` at the project root.

```toml
[project]
requires-python = ">=3.11"

[tool.black]
line-length = 88
target-version = ["py311"]
extend-exclude = '''
(
  /migrations/
  | /generated/
)
'''
```

The main settings are:

| Setting | Meaning |
| :--- | :--- |
| `line-length` | Target number of characters per line |
| `target-version` | Python versions supported by the code being formatted |
| `extend-exclude` | Additional paths to exclude, such as generated files |

`target-version` describes **the Python version supported by the target code**, not the Python version used to run Black.

Start with Black's defaults before adding configuration. Changing settings only for a clear team requirement preserves Black's main benefit: reducing style debates.

---

## Format Automatically on Save in VS Code

Formatting on save makes Black harder to forget than manually running `black .` in a terminal.

Install the **Black Formatter** extension in VS Code and add the following to `.vscode/settings.json`:

```json
{
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.formatOnSave": true
  }
}
```

Black will now run whenever a Python file is saved.

Save-time formatting alone is not enough, however. Team members without the extension, or AI agents, can still commit unformatted code. A CI check provides a reliable final guard.

---

## Format Before Commits with pre-commit

Use `pre-commit` to run Black automatically before each commit.

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/psf/black-pre-commit-mirror
    rev: 26.5.1
    hooks:
      - id: black
        language_version: python3.11
```

Then enable the hook:

```bash
python -m pip install pre-commit
pre-commit install
```

Black will run before future `git commit` operations. If it reformats a file, review the change and commit again.

Pin the Black version in `rev`. Keeping local development, pre-commit, and CI on the same version reduces the risk of different environments producing different formatting.

---

## Detect Unformatted Code with GitHub Actions

To check Black on GitHub, add `.github/workflows/black.yml`:

```yaml
name: Black

on:
  push:
  pull_request:

jobs:
  black:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: psf/black@stable
        with:
          options: "--check --diff"
          src: "."
          version: "26.5.1"
```

The check fails when the repository contains unformatted code and displays Black's proposed changes as a diff.

CI should generally report formatting problems with `--check` rather than modifying files automatically. Apply and review the fix locally or through a development agent before committing it.

---

## Why Black Helps AI-Native Development

In AI-native application development, code is generated and edited by multiple AI agents as well as humans.

Different models may produce different styles, and detailed style instructions in a prompt still cannot guarantee complete consistency. Black normalizes the final output regardless of its source.

### 1. Shorter Prompts

There is no need to tell an AI to use double quotes, keep lines to 88 characters, or add trailing commas every time.

Leave style to Black and focus AI instructions on requirements, design, and error handling.

### 2. Code Reviews Can Focus on Logic

With fewer formatting-only changes, reviewers can more easily track meaningful changes such as:

- The prompt construction changed
- Timeout handling was added to the LLM API call
- The transaction boundary for log storage changed
- User input validation was added

### 3. Normalize Output Across Agents

Humans, code-generation AI, and refactoring agents can all write in different styles. Running Black at the end converts their work to the same format.

```bash
# AI generates or edits code

# Normalize formatting
black .

# Detect static issues
ruff check .

# Verify behavior
pytest
```

Black does not guarantee code quality in place of AI. It is valuable as a **mechanical step that absorbs formatting variation produced by AI**.

---

## Partially Disabling Black

When a special layout must be preserved, add `# fmt: skip` to exclude a single line.

```python
matrix = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]  # fmt: skip
```

For multiple lines, surround the block with `# fmt: off` and `# fmt: on`.

```python
# fmt: off
COMMAND_TABLE = {
    "start":  handle_start,
    "stop":   handle_stop,
    "status": handle_status,
}
# fmt: on
```

Too many exceptions undermine project consistency. Use them only when the layout itself carries meaning.

---

## Common Adoption Problems

### The First Run Produces a Huge Diff

Running Black for the first time in an existing project may change nearly every Python file.

Mixing that work with a functional change makes review difficult. **Put the initial Black formatting in its own commit or pull request.**

```bash
black .
git add .
git commit -m "Apply Black formatting"
```

### Different Team Members Get Different Results

Black's broad style remains stable, but small formatting details can change between versions.

Align the Black version used in dependencies, pre-commit, and CI. When upgrading, update all environments together.

### Black Does Not Sort Imports

Black formats the appearance of import statements, but it does not sort standard-library, third-party, and local imports.

Use Ruff's import rules or isort for import ordering. When using isort, configure `profile = "black"` to avoid conflicts.

```toml
[tool.isort]
profile = "black"
```

### Assuming Black Makes the Code Safe

Black normally performs a safety check to confirm that the syntax tree is effectively unchanged after formatting. This is not a test of application correctness.

Authentication, authorization, billing, LLM output validation, and database updates still require separate tests and review.

---

## Recommended Minimal Setup

An individual developer or small team does not need a complicated configuration.

### 1. Add Black as a Development Dependency

```bash
uv add --dev black
```

### 2. Specify Only the Target Version in pyproject.toml

```toml
[tool.black]
target-version = ["py311"]
```

### 3. Enable Formatting on Save in VS Code

```json
{
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.formatOnSave": true
  }
}
```

### 4. Reject Unformatted Code in CI

```bash
black --check .
```

With this setup, code is normally formatted on save and CI catches anything that slips through.

---

## Summary

| Point | Details |
| :--- | :--- |
| **What Black is** | A formatter that automatically standardizes the appearance of Python code |
| **What it formats** | Whitespace, line breaks, indentation, quotes, and trailing commas |
| **What it does not do** | Bug detection, type checking, testing, or performance optimization |
| **Basic command** | `black .` |
| **Check only** | `black --check --diff .` |
| **Configuration file** | `[tool.black]` in `pyproject.toml` |
| **Value in AI development** | Automatically normalizes style differences between humans and multiple AIs |

Black's real value is not limited to making code look clean.

It creates a working environment where a team can **stop debating which style is correct and focus on design, logic, and tests**.

As AI writes more code, a mechanical step that returns generated output to a consistent format becomes increasingly important. Black provides a simple and reproducible foundation for that process.

---

## References

- [Black Documentation](https://black.readthedocs.io/en/stable/)
- [Black — Getting Started](https://black.readthedocs.io/en/stable/getting_started.html)
- [Black — Usage and Configuration](https://black.readthedocs.io/en/stable/usage_and_configuration/the_basics.html)
- [Black — The Black Code Style](https://black.readthedocs.io/en/stable/the_black_code_style/current_style.html)
- [Black — Version Control Integration](https://black.readthedocs.io/en/stable/integrations/source_version_control.html)
- [Black — GitHub Actions Integration](https://black.readthedocs.io/en/stable/integrations/github_actions.html)
- [psf/black GitHub Repository](https://github.com/psf/black)
