"""Mythos/Fable の記事に入れるベンチマーク比較図を生成する。

指標ごとに桁が違うので1本の軸に載せず、指標ごとに独立した横軸を持つ
small multiples にしている。値は記事本文と同じ Anthropic 公表値。
"""

from common import (PAD, S1, S2, VB_W, bar_panel, footnote, heading, svg, write)

SLUG = "2026-06-10-claude-mythos-fable"

LABEL_W = 62                    # 行ラベルの幅
PX0, PX1 = PAD + LABEL_W, VB_W - 46

PANELS = [
    # (パネル見出し, 横軸の最大値, 目盛り間隔, [(行ラベル, 値, 色)])
    ("Cognition FrontierCode / Diamond", 40, 20,
     [("Fable 5", 29.3, S1), ("Opus 4.8", 13.4, S2)]),
    ("Hex 主要分析ベンチマーク", 100, 50,
     [("Fable 5", 90.0, S1), ("Opus 4.8", None, S2)]),
]


def benchmark_comparison():
    b, y = heading("Fable 5 と Opus 4.8 のベンチマーク", [
        "FrontierCode Diamond では Opus 4.8 の約2.2倍。",
    ])

    y += 6
    for title, vmax, step, rows in PANELS:
        els, y = bar_panel(y, title, rows, vmax, step, PX0, PX1,
                           vfmt=lambda v: f"{v}%", tfmt=lambda v: f"{int(v)}%",
                           row_h=30, missing="公表値なし")
        b += els

    notes, y = footnote([
        "出典: Anthropic の公表値（2026年6月時点）。",
        "独立した再現検証は十分ではない。",
        "指標ごとに横軸のスケールが異なる。",
    ], y + 6)
    b += notes

    return svg(y + 2, "bm",
               "Claude Fable 5 と Claude Opus 4.8 のベンチマーク比較",
               "Cognition FrontierCode の Diamond レベルで Fable 5 が29.3%、Opus 4.8 が13.4%。"
               "Hex の主要分析ベンチマークでは Fable 5 が90%で、Opus 4.8 の該当スコアは公表されていない。"
               "出典はAnthropicの公表値（2026年6月時点）。",
               "\n".join(b) + "\n")


if __name__ == "__main__":
    write(SLUG, "benchmark-comparison.svg", benchmark_comparison())
