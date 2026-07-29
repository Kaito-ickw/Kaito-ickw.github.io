"""Felix Craft 記事の図を生成する。

収益の数値は Felix Craft / Nat Eliason の公開レポートと OpenClaw.report の集計
（2026年3月初旬時点の累計）。_data/stale_watch.yml の対象記事なので、本文を
更新するときはここも直して再生成する。

Stripe内訳の「その他」は、Stripe合計からガイドPDFとClaw Martを引いた差分。
Clawcommerce（受託）などが入るが、内訳の公表値がないためまとめている。
"""

from common import (INK, PAD, S1, S2, S3, VB_W,
                    bar_panel, footnote, heading, svg, write)
from diagram import Section, figure, write_figure

SLUG = "2026-07-29-felix-craft-autonomy"

STRIPE_TOTAL = 100570
CRYPTO_TOTAL = 94973
PDF_SALES = 41000
CLAWMART = 14000
OTHER = STRIPE_TOTAL - PDF_SALES - CLAWMART

LABEL_W = 74
PX0, PX1 = PAD + LABEL_W, VB_W - 58


def _k(v):
    return f"${v/1000:.0f}k"


def revenue_breakdown():
    b, y = heading("Felixの累計収益の内訳", [
        "約半分はプロダクト売上ではなく、",
        "自分の名前を冠したトークン由来。",
    ])
    y += 6

    els, y = bar_panel(y, "収益の源泉", [
        ("Stripe決済", STRIPE_TOTAL, S1),
        ("暗号資産", CRYPTO_TOTAL, S2),
    ], 120000, 60000, PX0, PX1, vfmt=_k, tfmt=_k)
    b += els

    els, y = bar_panel(y, "Stripe決済の内訳", [
        ("ガイドPDF", PDF_SALES, S1),
        ("Claw Mart", CLAWMART, S2),
        ("その他", OTHER, S3),
    ], 60000, 30000, PX0, PX1, vfmt=_k, tfmt=_k)
    b += els

    notes, y = footnote([
        "出典: Felix Craft と Nat Eliason の公開レポート、",
        "OpenClaw.report の集計（2026年3月初旬時点の累計）。",
        "「その他」はStripe合計からの差分で、受託などを含む。",
        "パネルごとに横軸のスケールが異なる。",
    ], y + 4)
    b += notes

    return svg(y + 2, "rb",
               "Felixの累計収益の内訳",
               "収益の源泉はStripe決済が約100,570ドル、暗号資産が約94,973ドルで、"
               "半分近くが$FELIXトークンの取引手数料などプロダクト外の収入である。"
               "Stripe決済の内訳は、29ドルのガイドPDFが約41,000ドル、"
               "スキル市場Claw Martが約14,000ドル、受託などのその他が約45,570ドル。"
               "出典はFelix CraftとNat Eliasonの公開レポート、"
               "およびOpenClaw.reportの集計（2026年3月初旬時点の累計）。",
               "\n".join(b) + "\n")


write_figure(SLUG, "autonomy-boundary.svg", figure(
    "felixloop",
    "Felixのループと人間の介入点",
    "Natが音声メモで方針を渡すと、Felixが計画を立て、サブエージェントのIrisとRemyが"
    "サポートと営業を実行する。コード作成、デプロイ、決済処理はFelixが人手を介さず行う。"
    "外部公開にあたるXの投稿だけは人間の承認を通す。"
    "夜間の自己改善ループで、その日に人間の手が必要だった箇所を洗い出し、"
    "自動化の範囲を広げてから翌日の計画へ戻る。",
    [Section(
        nodes=[("nat", "Natの音声メモ（方針）", "warm"),
               ("plan", "Felixが計画を立てる", "accent"),
               ("sub", "Iris（サポート）\nRemy（営業）"),
               ("exec", "実装・デプロイ・決済処理"),
               ("gate", "外部公開は承認", "decision"),
               ("night", "夜間の自己改善ループ")],
        edges=[("nat", "plan"), ("plan", "sub"), ("sub", "exec"),
               ("exec", "gate"), ("gate", "night"),
               ("night", "plan", "自動化の範囲を広げる")],
    ),
     Section(
        title="人間が握り続けているもの",
        framed=True,
        chips=["戦略と market positioning", "X投稿の原文",
               "法務・銀行・税務", "配信力（フォロワー）"],
        chip_style="plain",
    )]))

if __name__ == "__main__":
    write(SLUG, "revenue-breakdown.svg", revenue_breakdown())
