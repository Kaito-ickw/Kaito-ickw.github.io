"""ハーネスエンジニアリングの記事の構造図を生成する（日英）。

入れ子の包含＋中央配置は Mermaid だと崩れやすいので SVG で描いている。
スマホの幅に合わせて縦長のレイアウトにしてある。
"""

from common import (BLUE_ACCENT, INK, INK2, LINE, PAD, SHELL, SOFT, SURF, VB_W,
                    heading, svg, text, write)

SLUG = "2026-06-08-harness-engineering-guide"

TEXT = {
    "ja": dict(
        title="ハーネスの構造",
        sub=["モデルは、指示・Hooks・権限・ツール範囲に",
             "囲まれた環境の中で動く。"],
        shell="ハーネス",
        model="モデル / LLM",
        rows=[
            ("CLAUDE.md / AGENTS.md", "エージェントへの指示・コンテキスト"),
            ("Hooks", "PreToolUse / PostToolUse / Stop"),
            ("Permissions", "ツール実行ポリシー"),
            ("Tool Surface", "公開するツールの範囲"),
        ],
        evaluation=("Evaluation", "テスト・トレース・Human-in-the-loop"),
        svgtitle="Claude Code を例にしたハーネスの構造図",
        svgdesc="ハーネスという外枠の中に、CLAUDE.md / AGENTS.md（エージェントへの指示・コンテキスト）、"
                "Hooks（PreToolUse / PostToolUse / Stop）、Permissions（ツール実行ポリシー）、"
                "Tool Surface（公開するツールの範囲）の4層が積まれている。その下に双方向の矢印を挟んで"
                "モデル / LLM が置かれ、さらに下に Evaluation（テスト・トレース・Human-in-the-loop）が置かれている。",
    ),
    "en": dict(
        title="The structure of a harness",
        sub=["The model runs inside an environment bounded by",
             "instructions, hooks, permissions and tool surface."],
        shell="Harness",
        model="Model / LLM",
        rows=[
            ("CLAUDE.md / AGENTS.md", "Instructions and context for the agent"),
            ("Hooks", "PreToolUse / PostToolUse / Stop"),
            ("Permissions", "Tool execution policy"),
            ("Tool Surface", "Range of exposed tools"),
        ],
        evaluation=("Evaluation", "Tests / traces / human-in-the-loop"),
        svgtitle="Diagram of a harness structure, using Claude Code as an example",
        svgdesc="An outer box labelled Harness contains four stacked layers: CLAUDE.md / AGENTS.md "
                "(instructions and context for the agent), Hooks (PreToolUse / PostToolUse / Stop), "
                "Permissions (tool execution policy), and Tool Surface (range of exposed tools). Below them, "
                "connected by a two-way arrow, sits Model / LLM, and below that Evaluation "
                "(tests / traces / human-in-the-loop).",
    ),
}

SHELL_X, SHELL_W = 8, VB_W - 16
BOX_X, BOX_W = 20, VB_W - 40
ROW_H = 44


def _arrow(x, y0, y1):
    """上下に矢じりを持つ縦の双方向矢印。"""
    return (
        f'<line x1="{x}" y1="{y0+6}" x2="{x}" y2="{y1-6}" stroke="{INK2}" stroke-width="1.5"/>'
        f'<path d="M{x-5},{y0+7} L{x},{y0} L{x+5},{y0+7} Z" fill="{INK2}"/>'
        f'<path d="M{x-5},{y1-7} L{x},{y1} L{x+5},{y1-7} Z" fill="{INK2}"/>'
    )


def _row(y, name, sub):
    return [
        f'<rect x="{BOX_X}" y="{y+9}" width="4" height="{ROW_H-18}" rx="2" fill="{BLUE_ACCENT}"/>',
        text(BOX_X + 16, y + 20, name, "label", INK, 600),
        text(BOX_X + 16, y + 35, sub, "note", INK2),
    ]


def harness_structure(lang):
    t = TEXT[lang]
    b, y = heading(t["title"], t["sub"])

    shell_top = y + 6
    layers_top = shell_top + 34
    layers_h = ROW_H * len(t["rows"])
    model_top = layers_top + layers_h + 22
    eval_top = model_top + 32 + 22
    eval_h = ROW_H
    shell_bottom = eval_top + eval_h + 14

    b.append(f'<rect x="{SHELL_X}" y="{shell_top}" width="{SHELL_W}" height="{shell_bottom-shell_top}" '
             f'rx="10" fill="{SHELL}" stroke="{LINE}" stroke-width="1.5"/>')
    b.append(text(SHELL_X + 14, shell_top + 22, t["shell"], "panel", INK2, 700))

    b.append(f'<rect x="{BOX_X}" y="{layers_top}" width="{BOX_W}" height="{layers_h}" '
             f'rx="8" fill="{SURF}" stroke="{SOFT}" stroke-width="1.5"/>')
    for i, (name, sub) in enumerate(t["rows"]):
        y = layers_top + i * ROW_H
        if i:
            b.append(f'<line x1="{BOX_X}" y1="{y}" x2="{BOX_X+BOX_W}" y2="{y}" stroke="{SOFT}" stroke-width="1.5"/>')
        b += _row(y, name, sub)

    b.append(_arrow(VB_W // 2, layers_top + layers_h, model_top))
    b.append(f'<rect x="{VB_W//2-80}" y="{model_top}" width="160" height="32" rx="16" fill="{BLUE_ACCENT}"/>')
    b.append(text(VB_W // 2, model_top + 21, t["model"], "label", "#ffffff", 600, "middle"))
    b.append(_arrow(VB_W // 2, model_top + 32, eval_top))

    b.append(f'<rect x="{BOX_X}" y="{eval_top}" width="{BOX_W}" height="{eval_h}" '
             f'rx="8" fill="{SURF}" stroke="{SOFT}" stroke-width="1.5"/>')
    b += _row(eval_top, *t["evaluation"])

    return svg(shell_bottom + 10, "hn", t["svgtitle"], t["svgdesc"], "\n".join(b) + "\n")


if __name__ == "__main__":
    write(SLUG, "harness-structure.svg", harness_structure("ja"))
    write(SLUG, "harness-structure-en.svg", harness_structure("en"))
