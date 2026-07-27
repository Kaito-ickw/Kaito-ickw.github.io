"""Kimi K3 比較記事に入れるベンチマーク図と価格図を生成する。

値は記事本文の表と同じ（Artificial Analysis と各社公表値、2026年7月時点）。
_data/stale_watch.yml の対象記事なので、本文を更新するときはここも直して再生成する。

Frontend Code Arena と GPQA Diamond は順位のみ・単独モデルのみで比較にならないため
棒グラフには載せていない。GDPval v2 の GPT-5.6 Sol は公表値がない。
"""

from common import (INK, PAD, S1, S2, S3, VB_W,
                    bar_panel, footnote, heading, legend_stacked, svg, write)

SLUG = "2026-07-20-kimi-k3-vs-fable-gpt"

MODELS = [("Kimi K3", S1), ("GPT-5.6 Sol", S2), ("Claude Fable 5", S3)]
SHORT = ["K3", "Sol", "Fable 5"]

LABEL_W = 52
PX0, PX1 = PAD + LABEL_W, VB_W - 56


def _rows(values):
    return [(s, v, c) for s, v, (_, c) in zip(SHORT, values, MODELS)]


def benchmark_comparison():
    b, y = heading("ベンチマークで見る位置づけ", [
        "3モデルはどの指標でも数%以内に収まる。",
        "領域ごとに首位が入れ替わる。",
    ])
    legend, y = legend_stacked(MODELS, y + 8)
    b += legend
    y += 6

    panels = [
        ("AA Intelligence Index（総合・%）", [57.1, 58.9, 59.9], 60, 30, lambda v: f"{v}%", lambda v: f"{int(v)}%"),
        ("FrontierSWE（コーディング）", [77.8, 77.6, 76.8], 80, 40, lambda v: f"{v}", lambda v: f"{int(v)}"),
        ("GDPval v2（実務作業）", [1668, None, 1760], 1800, 900, lambda v: f"{v}", lambda v: f"{int(v)}"),
    ]
    for title, vals, vmax, step, vfmt, tfmt in panels:
        els, y = bar_panel(y, title, _rows(vals), vmax, step, PX0, PX1,
                           vfmt=vfmt, tfmt=tfmt, missing="公表値なし")
        b += els

    notes, y = footnote([
        "出典: Artificial Analysis および各社公表値",
        "（2026年7月時点）。指標ごとに横軸のスケールが",
        "異なる。軸はいずれも0から始めている。",
    ], y + 6)
    b += notes

    return svg(y + 2, "bc",
               "Kimi K3・GPT-5.6 Sol・Claude Fable 5 のベンチマーク比較",
               "AA Intelligence Index は Kimi K3 が57.1%、GPT-5.6 Sol が58.9%、Claude Fable 5 が59.9%。"
               "FrontierSWE は Kimi K3 が77.8で首位、GPT-5.6 Sol が77.6、Claude Fable 5 が76.8。"
               "GDPval v2 は Kimi K3 が1,668、Claude Fable 5 が1,760で、GPT-5.6 Sol の公表値はない。"
               "いずれの指標でも3モデルの差は数%以内に収まっている。"
               "出典はArtificial Analysisおよび各社公表値（2026年7月時点）。",
               "\n".join(b) + "\n")


def pricing_comparison():
    b, y = heading("価格（$/1Mトークン）", [
        "Kimi K3 は Claude Fable 5 の約1/3。",
    ])
    legend, y = legend_stacked(MODELS, y + 8)
    b += legend
    y += 6

    for title, vals, vmax, step in [
        ("入力", [3, 5, 10], 10, 5),
        ("出力", [15, 30, 50], 50, 25),
    ]:
        els, y = bar_panel(y, title, _rows(vals), vmax, step, PX0, PX1,
                           vfmt=lambda v: f"${v}", tfmt=lambda v: f"${int(v)}")
        b += els

    notes, y = footnote([
        "出典: 各社公表の従量課金レート（2026年7月時点）。",
        "入力と出力で横軸のスケールが異なる。",
    ], y + 6)
    b += notes

    return svg(y + 2, "pc",
               "Kimi K3・GPT-5.6 Sol・Claude Fable 5 の価格比較",
               "入力は Kimi K3 が$3、GPT-5.6 Sol が$5、Claude Fable 5 が$10。"
               "出力は Kimi K3 が$15、GPT-5.6 Sol が$30、Claude Fable 5 が$50。"
               "いずれも Kimi K3 は Claude Fable 5 の約3分の1の価格になる。"
               "出典は各社公表の従量課金レート（2026年7月時点）。",
               "\n".join(b) + "\n")


if __name__ == "__main__":
    write(SLUG, "benchmark-comparison.svg", benchmark_comparison())
    write(SLUG, "pricing-comparison.svg", pricing_comparison())
