"""勝率と標本サイズの記事に入れる2枚の図を生成する。

1. 95%信頼区間（Wilson score）の数直線比較
2. 一様事前分布からベイズ更新した事後分布（ベータ分布）の重ね描き
"""

import math

from common import (AXIS, FS, GRID, INK, INK2, MUTED, PAD, S1, S2, SURF, VB_W,
                    footnote, heading, legend_stacked, svg, text, write)

SLUG = "2026-07-14-win-rate-sample-size-statistics"

PX0, PX1 = 30, VB_W - 20        # プロット領域の左右
sx = lambda v: PX0 + (PX1 - PX0) * v / 100.0


def confidence_interval():
    b, y = heading("本当の勝率の95%信頼区間", [
        "観測勝率は80%と60%で前者が高い。",
        "しかし区間の下限は38%と50%で逆転する。",
    ])

    grid_top = y + 4
    top = y + 10
    rows = [
        ("5回中4勝（観測80%）", 38, 96, 80, S1),
        ("100回中60勝（観測60%）", 50, 69, 60, S2),
    ]
    marks = []
    for label, lo, hi, obs, col in rows:
        marks.append(text(PAD, top + 12, label, "label", INK, 600))
        by = top + 24
        marks.append(f'<rect x="{sx(lo):.1f}" y="{by}" width="{sx(hi)-sx(lo):.1f}" height="22" rx="3" '
                     f'fill="{col}" fill-opacity="0.28"/>')
        for v in (lo, hi):
            marks.append(f'<line x1="{sx(v):.1f}" y1="{by-5}" x2="{sx(v):.1f}" y2="{by+27}" '
                         f'stroke="{col}" stroke-width="2.5"/>')
        marks.append(f'<circle cx="{sx(obs):.1f}" cy="{by+11}" r="5" fill="{col}" '
                     f'stroke="{SURF}" stroke-width="1.5"/>')
        marks.append(text(sx(lo), by + 43, f"{lo}%", "tick", INK, 600, "middle"))
        marks.append(text(sx(hi), by + 43, f"{hi}%", "tick", INK, 600, "middle"))
        top = by + 58

    axis_y = top + 4

    # グリッドは帯の背面に来るよう、マークより先に積む
    for v in range(0, 101, 25):
        b.append(f'<line x1="{sx(v):.1f}" y1="{grid_top}" x2="{sx(v):.1f}" y2="{axis_y}" '
                 f'stroke="{GRID}" stroke-width="1"/>')
    b += marks

    b.append(f'<line x1="{PX0}" y1="{axis_y}" x2="{PX1}" y2="{axis_y}" stroke="{AXIS}" stroke-width="1"/>')
    for v in range(0, 101, 25):
        b.append(text(sx(v), axis_y + 15, f"{v}%", "tick", MUTED, None, "middle"))
    b.append(text((PX0 + PX1) // 2, axis_y + 33, "本当の勝率", "tick", INK2, None, "middle"))

    notes, y = footnote(["丸は観測された勝率。区間はWilson score interval。"], axis_y + 52)
    b += notes

    return svg(y + 2, "ci",
               "5回中4勝と100回中60勝の95%信頼区間の比較",
               "本当の勝率の95%信頼区間を数直線上に並べた図。5回中4勝は38%から96%と幅が広く、"
               "100回中60勝は50%から69%と狭い。観測勝率は80%と60%で前者が高いが、"
               "信頼区間の下限は38%と50%で逆転している。",
               "\n".join(b) + "\n")


def _beta_pdf(x, a, b):
    if x <= 0 or x >= 1:
        return 0.0
    log_b = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
    return math.exp((a - 1) * math.log(x) + (b - 1) * math.log(1 - x) - log_b)


def beta_posterior():
    N = 300
    curves = [
        (5, 2, S1, "5回中4勝 → Beta(5, 2)", 5 / 7, "71%"),
        (61, 41, S2, "100回中60勝 → Beta(61, 41)", 61 / 102, "60%"),
    ]

    b, y = heading("本当の勝率の事後分布", [
        "標本が少ないほど山は平たく広がり、",
        "推定値は中央へ引き戻される。",
    ])
    legend, y = legend_stacked([(lab, col) for _, _, col, lab, _, _ in curves], y + 8)
    b += legend

    plot_top = y + 8
    base = plot_top + 130
    ymax = max(_beta_pdf(i / N, a, bb) for a, bb, *_ in curves for i in range(1, N)) * 1.10
    px = lambda x: PX0 + (PX1 - PX0) * x
    py = lambda v: base - (base - plot_top) * v / ymax

    for v in range(0, 101, 25):
        b.append(f'<line x1="{px(v/100):.1f}" y1="{plot_top-6}" x2="{px(v/100):.1f}" y2="{base}" '
                 f'stroke="{GRID}" stroke-width="1"/>')

    for a, bb, col, _, _, _ in curves:
        pts = [f"{px(i/N):.1f},{py(_beta_pdf(i/N, a, bb)):.1f}" for i in range(N + 1)]
        b.append(f'<path d="M{px(0):.1f},{base} L' + " L".join(pts)
                 + f' L{px(1):.1f},{base} Z" fill="{col}" fill-opacity="0.18"/>')
        b.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{col}" '
                 f'stroke-width="2" stroke-linejoin="round"/>')

    # 平均（推定勝率）の位置
    for a, bb, col, _, mean, lab in curves:
        x = px(mean)
        b.append(f'<line x1="{x:.1f}" y1="{py(_beta_pdf(mean, a, bb)):.1f}" x2="{x:.1f}" y2="{base}" '
                 f'stroke="{col}" stroke-width="1.5" stroke-dasharray="4 4"/>')
    b.append(text(px(61 / 102) - 3, plot_top - 12, "60%", "tick", INK, 600, "end"))
    b.append(text(px(5 / 7) + 3, plot_top - 12, "71%", "tick", INK, 600, "start"))

    b.append(f'<line x1="{PX0}" y1="{base}" x2="{PX1}" y2="{base}" stroke="{AXIS}" stroke-width="1"/>')
    for v in range(0, 101, 25):
        b.append(text(px(v / 100), base + 15, f"{v}%", "tick", MUTED, None, "middle"))
    b.append(text((PX0 + PX1) // 2, base + 33, "本当の勝率", "tick", INK2, None, "middle"))

    notes, y = footnote([
        "縦軸は確率密度（相対的な高さのみ意味を持つ）。",
        "破線と上端の数値は各分布の平均＝推定勝率。",
    ], base + 52)
    b += notes

    return svg(y + 2, "beta",
               "5回中4勝と100回中60勝の事後分布の比較",
               "一様事前分布からベイズ更新した本当の勝率の事後分布を重ねた図。"
               "5回中4勝のBeta(5,2)は平均71%で幅広く平たい山になり、"
               "100回中60勝のBeta(61,41)は平均60%で鋭く尖った山になる。"
               "標本が少ないほど推定が定まらないことを示す。",
               "\n".join(b) + "\n")


if __name__ == "__main__":
    write(SLUG, "confidence-interval.svg", confidence_interval())
    write(SLUG, "beta-posterior.svg", beta_posterior())
