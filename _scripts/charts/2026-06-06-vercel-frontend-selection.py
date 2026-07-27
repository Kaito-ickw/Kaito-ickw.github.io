"""Vercel フロントエンド選定の記事に入れる帯域別コスト比較図を生成する（日英）。

値は各社公式料金ページの確認結果。料金は変わりやすいので
_data/stale_watch.yml のレビュー時にここを更新して再生成する。

  Vercel Pro       $20/月・1シート、帯域1TB込み、超過 $0.15/GB
  Cloudflare Pages Workers Paid $5/月、帯域は実質無制限
  Netlify Pro      $20/月・3,000クレジット込み、帯域20クレジット/GB、
                   追加クレジット 1,500 あたり $10（≒ $0.13/GB）
"""

from common import (PAD, S1, S2, S3, VB_W, bar_panel, footnote, heading, svg, write)

SLUG = "2026-06-06-vercel-frontend-selection"

LABEL_W = 66
PX0, PX1 = PAD + LABEL_W, VB_W - 52
VMAX, STEP = 700, 350

# 帯域は10進TB（1TB = 1,000GB）で計算した月額。
COSTS = [
    [20, 5, 133],     # 1TB  Vercel: 込み枠内 / CF: 定額 / Netlify: 20 + 17,000クレジット
    [620, 5, 667],    # 5TB  Vercel: 20 + 4,000GB × $0.15 / Netlify: 20 + 97,000クレジット
]
COLS = [S1, S2, S3]

TEXT = {
    "ja": dict(
        title="ホスティング3社の月額コスト",
        sub=["1TB/月までは差がつかない。差が開くのは",
             "Vercel の込み枠を超えてから。"],
        panels=["帯域 1TB/月", "帯域 5TB/月"],
        rows=["Vercel Pro", "Cloudflare", "Netlify Pro"],
        note=["出典: 各社公式料金ページ（2026年7月時点）。",
              "Vercel Pro は1シート$20/月・帯域1TB込み、",
              "超過は$0.15/GB。Netlify Pro は$20/月・",
              "3,000クレジット込み、帯域20クレジット/GB。"],
        svgtitle="Vercel・Cloudflare Pages・Netlify の帯域別月額コスト比較",
        svgdesc="帯域1TB/月ではVercel Pro $20、Cloudflare Pages $5、Netlify Pro 約$133。"
                "帯域5TB/月ではVercel Pro 約$620、Cloudflare Pages $5、Netlify Pro 約$667。"
                "Cloudflare Pagesだけ帯域が増えても$5のまま変わらない。2026年7月時点の各社公式料金による。",
    ),
    "en": dict(
        title="Monthly cost of three hosts",
        sub=["At 1TB/month there is barely a gap. It opens",
             "once Vercel's included allowance runs out."],
        panels=["1TB / month", "5TB / month"],
        rows=["Vercel Pro", "Cloudflare", "Netlify Pro"],
        note=["Source: official pricing pages (July 2026).",
              "Vercel Pro is $20/month per seat with 1TB",
              "included, then $0.15/GB. Netlify Pro is $20 with",
              "3,000 credits; bandwidth costs 20 credits/GB."],
        svgtitle="Monthly cost of Vercel, Cloudflare Pages and Netlify by bandwidth",
        svgdesc="At 1TB/month: Vercel Pro $20, Cloudflare Pages $5, Netlify Pro about $133. "
                "At 5TB/month: Vercel Pro about $620, Cloudflare Pages $5, Netlify Pro about $667. "
                "Only Cloudflare Pages stays at $5 as bandwidth grows. Based on official pricing as of July 2026.",
    ),
}


def bandwidth_cost(lang):
    t = TEXT[lang]
    b, y = heading(t["title"], t["sub"])
    y += 6

    for ptitle, vals in zip(t["panels"], COSTS):
        rows = [(n, v, c) for n, v, c in zip(t["rows"], vals, COLS)]
        els, y = bar_panel(y, ptitle, rows, VMAX, STEP, PX0, PX1,
                           vfmt=lambda v: f"${v}", tfmt=lambda v: f"${int(v)}")
        b += els

    notes, y = footnote(t["note"], y + 6)
    b += notes

    return svg(y + 2, "hc", t["svgtitle"], t["svgdesc"], "\n".join(b) + "\n")


if __name__ == "__main__":
    write(SLUG, "bandwidth-cost.svg", bandwidth_cost("ja"))
    write(SLUG, "bandwidth-cost-en.svg", bandwidth_cost("en"))
