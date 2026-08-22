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


BENCH_TEXTS = {
    "ja": {
        "heading": ("ベンチマークで見る位置づけ", [
            "3モデルはどの指標でも数%以内に収まる。",
            "領域ごとに首位が入れ替わる。",
        ]),
        "panels": ["AA Intelligence Index（総合・%）", "FrontierSWE（コーディング）", "GDPval v2（実務作業）"],
        "missing": "公表値なし",
        "footnote": [
            "出典: Artificial Analysis および各社公表値",
            "（2026年7月時点）。指標ごとに横軸のスケールが",
            "異なる。軸はいずれも0から始めている。",
        ],
        "title": "Kimi K3・GPT-5.6 Sol・Claude Fable 5 のベンチマーク比較",
        "desc": "AA Intelligence Index は Kimi K3 が57.1%、GPT-5.6 Sol が58.9%、Claude Fable 5 が59.9%。"
                "FrontierSWE は Kimi K3 が77.8で首位、GPT-5.6 Sol が77.6、Claude Fable 5 が76.8。"
                "GDPval v2 は Kimi K3 が1,668、Claude Fable 5 が1,760で、GPT-5.6 Sol の公表値はない。"
                "いずれの指標でも3モデルの差は数%以内に収まっている。"
                "出典はArtificial Analysisおよび各社公表値（2026年7月時点）。",
    },
    "en": {
        "heading": ("Benchmark standings", [
            "All three sit within a few %.",
            "The leader shifts by domain.",
        ]),
        "panels": ["AA Intelligence Index (overall, %)", "FrontierSWE (coding)", "GDPval v2 (knowledge work)"],
        "missing": "not published",
        "footnote": [
            "Source: Artificial Analysis and vendor",
            "figures (July 2026). Horizontal scales",
            "differ per metric. All axes start at 0.",
        ],
        "title": "Benchmark comparison of Kimi K3, GPT-5.6 Sol, and Claude Fable 5",
        "desc": "AA Intelligence Index: Kimi K3 57.1%, GPT-5.6 Sol 58.9%, Claude Fable 5 59.9%. "
                "FrontierSWE: Kimi K3 leads at 77.8, GPT-5.6 Sol 77.6, Claude Fable 5 76.8. "
                "GDPval v2: Kimi K3 1,668 vs Claude Fable 5 1,760; no published GPT-5.6 Sol figure. "
                "All three models are within a few percent on every metric. "
                "Source: Artificial Analysis and vendor figures as of July 2026.",
    },
}


def benchmark_comparison(lang="ja"):
    t = BENCH_TEXTS[lang]
    b, y = heading(*t["heading"])
    legend, y = legend_stacked(MODELS, y + 8)
    b += legend
    y += 6

    panels = [
        (t["panels"][0], [57.1, 58.9, 59.9], 60, 30, lambda v: f"{v}%", lambda v: f"{int(v)}%"),
        (t["panels"][1], [77.8, 77.6, 76.8], 80, 40, lambda v: f"{v}", lambda v: f"{int(v)}"),
        (t["panels"][2], [1668, None, 1760], 1800, 900, lambda v: f"{v}", lambda v: f"{int(v)}"),
    ]
    for title, vals, vmax, step, vfmt, tfmt in panels:
        els, y = bar_panel(y, title, _rows(vals), vmax, step, PX0, PX1,
                           vfmt=vfmt, tfmt=tfmt, missing=t["missing"])
        b += els

    notes, y = footnote(t["footnote"], y + 6)
    b += notes

    return svg(y + 2, "bc", t["title"], t["desc"], "\n".join(b) + "\n")


PRICE_TEXTS = {
    "ja": {
        "heading": ("価格（$/1Mトークン）", [
            "Kimi K3 は Claude Fable 5 の約1/3。",
        ]),
        "panels": ["入力", "出力"],
        "footnote": [
            "出典: 各社公表の従量課金レート（2026年7月時点）。",
            "入力と出力で横軸のスケールが異なる。",
        ],
        "title": "Kimi K3・GPT-5.6 Sol・Claude Fable 5 の価格比較",
        "desc": "入力は Kimi K3 が$3、GPT-5.6 Sol が$5、Claude Fable 5 が$10。"
                "出力は Kimi K3 が$15、GPT-5.6 Sol が$30、Claude Fable 5 が$50。"
                "いずれも Kimi K3 は Claude Fable 5 の約3分の1の価格になる。"
                "出典は各社公表の従量課金レート（2026年7月時点）。",
    },
    "en": {
        "heading": ("Price ($/1M tokens)", [
            "Kimi K3 costs ~1/3 of Fable 5.",
        ]),
        "panels": ["Input", "Output"],
        "footnote": [
            "Source: vendor pay-as-you-go rates",
            "(July 2026). Horizontal scales differ",
            "between input and output.",
        ],
        "title": "Price comparison of Kimi K3, GPT-5.6 Sol, and Claude Fable 5",
        "desc": "Input: Kimi K3 $3, GPT-5.6 Sol $5, Claude Fable 5 $10. "
                "Output: Kimi K3 $15, GPT-5.6 Sol $30, Claude Fable 5 $50. "
                "Kimi K3 is roughly one third the price of Claude Fable 5 on both. "
                "Source: vendor pay-as-you-go rates as of July 2026.",
    },
}


def pricing_comparison(lang="ja"):
    t = PRICE_TEXTS[lang]
    b, y = heading(*t["heading"])
    legend, y = legend_stacked(MODELS, y + 8)
    b += legend
    y += 6

    for title, vals, vmax, step in [
        (t["panels"][0], [3, 5, 10], 10, 5),
        (t["panels"][1], [15, 30, 50], 50, 25),
    ]:
        els, y = bar_panel(y, title, _rows(vals), vmax, step, PX0, PX1,
                           vfmt=lambda v: f"${v}", tfmt=lambda v: f"${int(v)}")
        b += els

    notes, y = footnote(t["footnote"], y + 6)
    b += notes

    return svg(y + 2, "pc", t["title"], t["desc"], "\n".join(b) + "\n")


if __name__ == "__main__":
    write(SLUG, "benchmark-comparison.svg", benchmark_comparison())
    write(SLUG, "pricing-comparison.svg", pricing_comparison())
    write(SLUG, "benchmark-comparison-en.svg", benchmark_comparison("en"))
    write(SLUG, "pricing-comparison-en.svg", pricing_comparison("en"))
