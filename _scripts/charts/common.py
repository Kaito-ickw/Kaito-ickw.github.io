"""記事に埋め込むSVG図の共通パーツ。

## サイズの考え方（重要）

図は `<img>` として一様に拡縮されるだけなので、座標系の単位は「モバイルでの実px」に
近いところへ取る。記事本文での実表示幅は次のとおり。

    デスクトップ  約860px（$content-width 920px から余白を引いた値）
    スマホ        約330px（390px幅の端末）

そのまま置くとデスクトップはモバイルの2.6倍になり、モバイルに合わせると
デスクトップで文字が巨大になる。そこで `.chart` クラスで表示幅を560pxに抑えている
（`_sass/misc/chart.scss`）。この前提での倍率は以下。

    viewBox幅 400 →  モバイル 0.83倍 / デスクトップ 1.40倍

FS の各値はこの倍率で「モバイルで読める下限」を満たすように決めてある。
勝手に小さくしないこと。文字を小さくしたくなったら、まず図の情報量を減らす。

## 密度の目安（viewBox幅 400）

- 1行のラベルは日本語で12文字、英数字で28文字まで
- 1枚の図に載せる系列は3つまで。4つ以上はパネルを分ける
- 目盛りは5本まで
- 横長より縦積みを優先する。スマホでは横幅だけが足りない
"""

import os

# ---------------------------------------------------------------- サーフェス・インク
SURF = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
SHELL = "#f0efec"

# ---------------------------------------------------------------- カテゴリカル（slot 1-3）
S1 = "#2a78d6"  # blue
S2 = "#eb6834"  # orange
S3 = "#1baf7a"  # aqua

# 構造図（グラフではない図）で使う別名
LINE = AXIS          # 外枠の罫線
SOFT = GRID          # 内側の仕切り線
BLUE_ACCENT = S1     # 見出しのアクセント・強調ノード

# ---------------------------------------------------------------- レイアウト
VB_W = 400           # viewBox の幅。全ての図で共通にする
PAD = 12             # 左右の余白

FS = {
    "title": 17,     # 図のタイトル
    "sub": 12,       # 図の説明
    "panel": 13,     # パネル見出し
    "label": 12,     # 系列名・行ラベル
    "value": 12,     # データラベル
    "tick": 11,      # 目盛り
    "note": 10,      # 脚注
}

FONT = '<style>text{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;}</style>'

# リポジトリルート（このファイルは _scripts/charts/ にある）
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
POSTS_IMG = os.path.join(ROOT, "assets", "images", "posts")


def svg(h, uid, title, desc, body):
    """title/desc 付きの SVG を組み立てる。幅は VB_W 固定。"""
    return (
        f'<svg viewBox="0 0 {VB_W} {h}" xmlns="http://www.w3.org/2000/svg" role="img" '
        f'aria-labelledby="{uid}-title {uid}-desc">\n'
        f'<title id="{uid}-title">{title}</title>\n'
        f'<desc id="{uid}-desc">{desc}</desc>\n'
        f"{FONT}\n"
        f'<rect x="0" y="0" width="{VB_W}" height="{h}" rx="8" fill="{SURF}"/>\n'
        + body
        + "</svg>\n"
    )


def text(x, y, s, size="label", fill=INK, weight=None, anchor=None):
    a = f' text-anchor="{anchor}"' if anchor else ""
    w = f' font-weight="{weight}"' if weight else ""
    return f'<text x="{x}" y="{y}" font-size="{FS[size]}"{w}{a} fill="{fill}">{s}</text>'


def hbar(x, y, w, h, fill, r=3):
    """ベースラインに接地し、データ側の端だけ角を丸めた横棒。"""
    w = max(w, 0.01)
    r = min(r, w)
    return (
        f'<path d="M{x},{y} L{x+w-r:.1f},{y} Q{x+w:.1f},{y} {x+w:.1f},{y+r} '
        f'L{x+w:.1f},{y+h-r} Q{x+w:.1f},{y+h} {x+w-r:.1f},{y+h} L{x},{y+h} Z" fill="{fill}"/>'
    )


def heading(title, sub_lines, y=24):
    """タイトルと、折り返し済みの説明行。sub_lines は文字列のリスト。"""
    out = [text(PAD, y, title, "title", INK, 700)]
    y += 20
    for line in sub_lines:
        out.append(text(PAD, y, line, "sub", INK2))
        y += 16
    return out, y


def legend_stacked(items, y, x=PAD):
    """縦積みの凡例。横並びはスマホで溢れるので使わない。"""
    out = []
    for label, col in items:
        out.append(f'<rect x="{x}" y="{y-9}" width="10" height="10" rx="2" fill="{col}"/>')
        out.append(text(x + 16, y, label, "label", INK))
        y += 17
    return out, y


def bar_panel(y, title, rows, vmax, step, px0, px1,
              vfmt=str, tfmt=str, row_h=28, bar_h=18, missing=None):
    """横棒1パネル。指標ごとに桁が違う図は、これを縦に積んで small multiples にする。

    rows は (行ラベル, 値, 色) のリスト。値が None なら missing の文字を出す。
    軸は必ず0から始める。途中で切ると差が誇張されるため。
    戻り値は (要素のリスト, 次のy)。
    """
    sx = lambda v: px0 + (px1 - px0) * v / vmax
    out = [text(PAD, y + 12, title, "panel", INK2, 600)]
    gt = y + 20
    gb = gt + len(rows) * row_h + 4

    v = 0
    while v <= vmax + 1e-9:
        out.append(f'<line x1="{sx(v):.1f}" y1="{gt}" x2="{sx(v):.1f}" y2="{gb}" '
                   f'stroke="{GRID}" stroke-width="1"/>')
        v += step

    by = gt + (row_h - bar_h) / 2
    for label, val, col in rows:
        out.append(text(px0 - 8, by + bar_h - 4, label, "tick", INK2, None, "end"))
        if val is None:
            out.append(text(px0 + 4, by + bar_h - 4, missing or "—", "tick", MUTED))
        else:
            out.append(hbar(px0, by, max(sx(val) - px0, 1.5), bar_h, col))
            out.append(text(sx(val) + 6, by + bar_h - 3, vfmt(val), "value", INK, 600))
        by += row_h

    out.append(f'<line x1="{px0}" y1="{gb}" x2="{px1}" y2="{gb}" stroke="{AXIS}" stroke-width="1"/>')
    v = 0
    while v <= vmax + 1e-9:
        out.append(text(sx(v), gb + 14, tfmt(v), "tick", MUTED, None, "middle"))
        v += step

    return out, gb + 34


def footnote(lines, y):
    """出典・前提。1行は日本語34文字を超えないところで自分で折り返す。"""
    out = []
    for line in lines:
        out.append(text(PAD, y, line, "note", MUTED))
        y += 13
    return out, y


def write(slug, filename, content):
    d = os.path.join(POSTS_IMG, slug)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, filename)
    with open(path, "w") as f:
        f.write(content)
    print("wrote", os.path.relpath(path, ROOT))
