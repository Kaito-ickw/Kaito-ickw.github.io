"""構造図（フロー・関係図）を宣言から組み立てるレイアウトエンジン。

`common.py` がデータのグラフ用なのに対して、こちらは「箱と矢印」の図を扱う。
記事のMermaidをSVGへ移すために作った。使い方は `_scripts/charts/README.md` を参照。

    from diagram import Section, figure, write_figure

    write_figure("2026-06-13-nodejs-basics-for-vibe-coding", "npm-run-dev.svg",
        figure(
            uid="npm",
            title="npm run dev が実行されるまで",
            desc="AIエージェントがnpm run devを実行し、……",
            sections=[Section(nodes=[...], edges=[...])],
        ))

## 設計の前提

- `viewBox` の幅は `common.VB_W`（400）で固定。実表示はモバイル330px / デスクトップ560px
- 文字サイズは `common.FS` から取る。ノード内は label(12) か tick(11)、辺のラベルは note(10)
- 層に置けるノード数が増えると1枚あたりの幅が痩せる。70pxを切る場合は自動で行を折る
- Mermaidの `subgraph` は横に並んで幅が倍になるので、ここでは Section として縦に積む

## 座標系

上から下へ層を積む。各層は横並び。辺は直交（縦→横→縦）で結び、角だけ丸める。
ループのように上へ戻る辺は、左右どちらかに確保したチャネルを通して迂回させる。
"""

import os
import sys

from common import (
    VB_W, PAD, FS, SURF, INK, INK2, MUTED, GRID, AXIS, SHELL,
    S1, S2, S3, LINE, SOFT, FONT, POSTS_IMG, ROOT, est_width, text,
)

# ---------------------------------------------------------------- 寸法
NODE_GAP_X = 12          # 同じ層のノード同士の横の間隔
NODE_GAP_X_TIGHT = 8     # 4つ以上並ぶ層で使う
LAYER_GAP = 26           # 層と層の縦の間隔（辺のラベルがない場合）
LAYER_GAP_LABELED = 40   # 辺にラベルがある場合
NODE_PAD_X = 8           # ノード内の左右余白
NODE_PAD_Y = 8
NODE_MIN_W = 70          # これを下回るなら層を折り返す
NODE_MIN_H = 30
CHANNEL_W = 16           # 戻り辺を通す左右のチャネル
CORNER_R = 7             # 直交する辺の角丸
ARROW = 6                # 矢じりの長さ

# ---------------------------------------------------------------- ノードの見た目
STYLES = {
    # name:      (塗り,       枠,     文字,  太さ)
    "box":       (SHELL,      LINE,   INK,   None),
    "accent":    ("#eaf1fb",  S1,     INK,   600),
    "warm":      ("#fdf1eb",  S2,     INK,   None),
    "cool":      ("#eef8f4",  S3,     INK,   None),
    "plain":     (SURF,       LINE,   INK2,  None),
    "decision":  ("#fcfaf4",  AXIS,   INK,   None),
}


def _fmt(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


# ---------------------------------------------------------------- テキスト折り返し
def _tokens(s):
    """折り返しの単位へ分解する。英数字は語単位、日本語は1文字単位。"""
    out, buf = [], ""
    for ch in s:
        if ord(ch) > 0x2E80:            # 日本語・全角
            if buf:
                out.append(buf)
                buf = ""
            out.append(ch)
        elif ch == " ":
            if buf:
                out.append(buf)
                buf = ""
            out.append(" ")
        else:
            buf += ch
    if buf:
        out.append(buf)
    return out


_NO_HEAD = "。、）」』】〉・？！"   # 行頭に来てはいけない文字
_NO_TAIL = "（「『【〈"


def wrap(s, max_w, size):
    """`max_w` に収まるように折り返す。`\\n` は明示的な改行として扱う。"""
    lines = []
    for para in s.split("\n"):
        cur = ""
        for tok in _tokens(para):
            cand = cur + tok
            if cur and est_width(cand.strip(), size) > max_w:
                if tok in _NO_HEAD and cur:      # ぶら下げ
                    cur = cand
                    continue
                if cur.rstrip() and cur.rstrip()[-1] in _NO_TAIL:
                    cur = cand
                    continue
                lines.append(cur.strip())
                cur = "" if tok == " " else tok
            else:
                cur = cand
        lines.append(cur.strip())
    lines = [ln for ln in lines if ln != ""] or [""]
    return _unwidow(lines, max_w, size)


def _unwidow(lines, max_w, size):
    """最終行に1文字だけ残る割れ方を避ける。前の行から1文字ぶん送る。"""
    if len(lines) < 2 or len(lines[-1]) != 1:
        return lines
    prev = lines[-2]
    if len(prev) < 3 or prev[-1] == " ":
        return lines
    moved = prev[-1] + lines[-1]
    if est_width(moved, size) > max_w:
        return lines
    return lines[:-2] + [prev[:-1].rstrip(), moved]


def fit(label, box_w, sizes=("label", "tick")):
    """箱の幅に収まる最大の文字サイズと、その折り返し結果を返す。

    どのサイズでも収まらない場合は、いちばん小さいサイズの結果を返す。
    はみ出しは check.py が拾うので、ここでは黙って縮めない。
    """
    avail = box_w - NODE_PAD_X * 2
    last = None
    for size in sizes:
        lines = wrap(label, avail, FS[size])
        last = (size, lines)
        if all(est_width(ln, FS[size]) <= avail for ln in lines):
            return size, lines
    return last


# ---------------------------------------------------------------- 図形
def node_box(x, y, w, h, lines, size, style):
    fill, stroke, fg, weight = STYLES[style]
    out = [f'<rect x="{_fmt(x)}" y="{_fmt(y)}" width="{_fmt(w)}" height="{_fmt(h)}" rx="6" '
           f'fill="{fill}" stroke="{stroke}" stroke-width="1"/>']
    out += _lines(x + w / 2, y, h, lines, size, fg, weight)
    return out


def node_hex(x, y, w, h, lines, size, style):
    """分岐（Mermaidの菱形）。菱形は日本語だと文字の置き場がないので六角形にする。"""
    fill, stroke, fg, weight = STYLES[style]
    n = min(13.0, w * 0.11)
    pts = " ".join(_fmt(a) + "," + _fmt(b) for a, b in [
        (x + n, y), (x + w - n, y), (x + w, y + h / 2),
        (x + w - n, y + h), (x + n, y + h), (x, y + h / 2),
    ])
    out = [f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="1"/>']
    out += _lines(x + w / 2, y, h, lines, size, fg, weight)
    return out


def _lines(cx, y, h, lines, size, fg, weight):
    lh = FS[size] + 3
    top = y + h / 2 - (len(lines) - 1) * lh / 2 + FS[size] / 2 - 1.5
    return [text(_fmt(cx), _fmt(top + i * lh), ln, size, fg, weight, "middle")
            for i, ln in enumerate(lines)]


def _arrow_head(x, y, direction, color):
    """先端(x,y)へ向かう矢じり。direction は down/up/left/right。"""
    a = ARROW
    if direction == "down":
        p = f"M{_fmt(x-3.6)},{_fmt(y-a)} L{_fmt(x+3.6)},{_fmt(y-a)} L{_fmt(x)},{_fmt(y)} Z"
    elif direction == "up":
        p = f"M{_fmt(x-3.6)},{_fmt(y+a)} L{_fmt(x+3.6)},{_fmt(y+a)} L{_fmt(x)},{_fmt(y)} Z"
    elif direction == "left":
        p = f"M{_fmt(x+a)},{_fmt(y-3.6)} L{_fmt(x+a)},{_fmt(y+3.6)} L{_fmt(x)},{_fmt(y)} Z"
    else:
        p = f"M{_fmt(x-a)},{_fmt(y-3.6)} L{_fmt(x-a)},{_fmt(y+3.6)} L{_fmt(x)},{_fmt(y)} Z"
    return f'<path d="{p}" fill="{color}"/>'


def _stroke(d, color, dashed=False, width=1.3):
    dash = ' stroke-dasharray="4 3"' if dashed else ""
    return (f'<path d="{d}" stroke="{color}" stroke-width="{width}" fill="none" '
            f'stroke-linejoin="round"{dash}/>')


def edge_ortho(x0, y0, x1, y1, color, dashed=False, both=False):
    """上の層から下の層へ。縦→横→縦で結び、角を丸める。

    both=True なら両端に矢じりを付ける（Mermaidの `<-->` にあたる双方向）。
    """
    end = y1 - ARROW
    head_up = [_arrow_head(x0, y0, "up", color)] if both else []
    if abs(x1 - x0) < 1.5:
        return [_stroke(f"M{_fmt(x0)},{_fmt(y0+ARROW if both else y0)} "
                        f"L{_fmt(x0)},{_fmt(end)}", color, dashed),
                _arrow_head(x1, y1, "down", color)] + head_up
    ym = (y0 + y1) / 2
    r = min(CORNER_R, abs(x1 - x0) / 2, (ym - y0), (end - ym))
    s = 1 if x1 > x0 else -1
    d = (f"M{_fmt(x0)},{_fmt(y0)} L{_fmt(x0)},{_fmt(ym-r)} "
         f"Q{_fmt(x0)},{_fmt(ym)} {_fmt(x0+r*s)},{_fmt(ym)} "
         f"L{_fmt(x1-r*s)},{_fmt(ym)} "
         f"Q{_fmt(x1)},{_fmt(ym)} {_fmt(x1)},{_fmt(ym+r)} "
         f"L{_fmt(x1)},{_fmt(end)}")
    return [_stroke(d, color, dashed), _arrow_head(x1, y1, "down", color)] + head_up


def edge_row(sx, sy, tx, ty, color, dashed=False):
    """同じ行に並ぶノード同士。横向きにまっすぐ結ぶ。"""
    s = 1 if tx > sx else -1
    return [_stroke(f"M{_fmt(sx)},{_fmt(sy)} L{_fmt(tx-ARROW*s)},{_fmt(ty)}", color, dashed),
            _arrow_head(tx, ty, "right" if s > 0 else "left", color)]


def edge_channel(sx, sy, tx, ty, channel_x, color, dashed=False):
    """箱を突き抜けてしまう辺を、左右に確保したチャネルへ迂回させる。

    上へ戻るループ辺と、層を飛び越す辺の両方をこれで描く。
    src の側面から出て、チャネルを縦に走り、dst の同じ側の側面へ入る。
    """
    s = 1 if channel_x > sx else -1
    up = ty < sy
    r = min(CORNER_R, abs(sy - ty) / 2)
    d = (f"M{_fmt(sx)},{_fmt(sy)} L{_fmt(channel_x-r*s)},{_fmt(sy)} "
         f"Q{_fmt(channel_x)},{_fmt(sy)} {_fmt(channel_x)},{_fmt(sy-r if up else sy+r)} "
         f"L{_fmt(channel_x)},{_fmt(ty+r if up else ty-r)} "
         f"Q{_fmt(channel_x)},{_fmt(ty)} {_fmt(channel_x-r*s)},{_fmt(ty)} "
         f"L{_fmt(tx+ARROW*s)},{_fmt(ty)}")
    return [_stroke(d, color, dashed),
            _arrow_head(tx, ty, "left" if s > 0 else "right", color)]


def _ortho_segments(x0, y0, x1, y1):
    """edge_ortho が通る線分。箱との当たり判定に使う。"""
    if abs(x1 - x0) < 1.5:
        return [(x0, y0, x0, y1)]
    ym = (y0 + y1) / 2
    return [(x0, y0, x0, ym), (x0, ym, x1, ym), (x1, ym, x1, y1)]


def _hits(segments, rects, margin=3):
    """線分がいずれかの矩形と交わるか。軸平行なので範囲の重なりだけ見る。"""
    for sx, sy, tx, ty in segments:
        lo_x, hi_x = min(sx, tx), max(sx, tx)
        lo_y, hi_y = min(sy, ty), max(sy, ty)
        for rx, ry, rw, rh in rects:
            if (lo_x < rx + rw + margin and hi_x > rx - margin
                    and lo_y < ry + rh + margin and hi_y > ry - margin):
                return True
    return False


def edge_label(x, y, label, anchor="middle"):
    """辺のラベル。線と重なるので背景を敷く。"""
    w = est_width(label, FS["note"]) + 8
    lx = {"middle": x - w / 2, "start": x - 4, "end": x - w + 4}[anchor]
    return [f'<rect x="{_fmt(lx)}" y="{_fmt(y-9)}" width="{_fmt(w)}" height="13" rx="3" '
            f'fill="{SURF}" opacity="0.95"/>',
            text(_fmt(x), _fmt(y + 1), label, "note", INK2, None, anchor)]


# ---------------------------------------------------------------- Section
class Section:
    """縦に積む単位。Mermaidの subgraph 1つぶんに相当する。

    nodes: (id, label) または (id, label, style)。style は STYLES のキー、
           分岐は "decision"（六角形で描く）
    edges: (src, dst) / (src, dst, label) / (src, dst, label, opts)
           opts は "dashed" を含む文字列。上へ戻る辺は自動で検出する
    layers: 層を明示したい場合に [[id, id], [id]] の形で渡す
    """

    def __init__(self, nodes=(), edges=(), title=None, framed=False, layers=None,
                 note=None, gap=None, chips=None, chip_style="box", steps=None):
        self.chips = chips
        self.chip_style = chip_style
        self.steps = steps
        self.nodes = [(n if len(n) == 3 else (n[0], n[1], "box")) for n in nodes]
        self.edges = [tuple(e) + ("",) * (3 - len(e)) if len(e) < 3 else tuple(e)
                      for e in edges]
        self.edges = [e if len(e) == 4 else e + ("",) for e in self.edges]
        self.title = title
        self.framed = framed
        self.layers_hint = layers
        self.note = note
        self.gap = gap


# ---------------------------------------------------------------- 層の割り当て
def _assign_layers(node_ids, edges):
    """辺の向きから層を決める。上へ戻る辺は除いてから最長経路で並べる。"""
    order = {n: i for i, n in enumerate(node_ids)}
    fwd, back = [], []
    # 宣言順で後ろへ向かう辺を前向き、前へ戻る辺を戻り辺とみなす。
    # Mermaidのソースは上から順に書かれているので、この判定で実用上そろう。
    for e in edges:
        (back if order[e[1]] <= order[e[0]] else fwd).append(e)

    layer = {n: 0 for n in node_ids}
    for _ in range(len(node_ids)):
        changed = False
        for src, dst, *_rest in fwd:
            if layer[dst] < layer[src] + 1:
                layer[dst] = layer[src] + 1
                changed = True
        if not changed:
            break
    return layer, set(id(e) for e in back)


def _order_layers(layer, node_ids):
    buckets = {}
    for n in node_ids:
        buckets.setdefault(layer[n], []).append(n)
    return [buckets[k] for k in sorted(buckets)]


def _split_row(row, avail):
    """1層に詰めすぎたら複数行へ折る。行あたりの数はできるだけ揃える。"""
    k = len(row)
    while k > 1:
        gap = NODE_GAP_X if k <= 3 else NODE_GAP_X_TIGHT
        if (avail - gap * (k - 1)) / k >= NODE_MIN_W:
            break
        k -= 1
    if k >= len(row):
        return [row]
    n_rows = -(-len(row) // k)          # 切り上げ
    per = -(-len(row) // n_rows)        # 3+2 のように均す
    # 折り返した行は「親の下にぶら下がる別の層」に見えてしまう。並列な列挙なら
    # Section(chips=[...]) を、そうでなければ図の分割を検討すること。
    print(f"  warn: 1層に{len(row)}個は多い。{n_rows}行へ折り返した: "
          f"{' / '.join(row)}", file=sys.stderr)
    return [row[i:i + per] for i in range(0, len(row), per)]


# ---------------------------------------------------------------- Section の描画
def _layout_section(sec, top, x0, x1):
    """1つの Section を (要素のリスト, 下端y) にする。

    チャネルを何本使うかは辺を引いてみるまで確定しないが、確保した本数だけ
    ノードの幅が痩せる。determined になるまで最大3回引き直す。
    """
    n = (0, 0)
    for _ in range(4):
        body, y, used = _layout_once(sec, top, x0, x1, n)
        if used == n:
            return body, y
        n = used
    return body, y


def _layout_once(sec, top, x0, x1, n_channels):
    n_left, n_right = n_channels
    body = []
    y = top
    inner_x0, inner_x1 = x0, x1

    if sec.framed:
        inner_x0, inner_x1 = x0 + 10, x1 - 10
    if sec.title:
        body.append(text(_fmt(inner_x0), _fmt(y + 14), sec.title, "panel", INK2, 600))
        y += 26
    elif sec.framed:
        y += 10

    if sec.chips:
        y = _layout_chips(sec, body, y, inner_x0, inner_x1)
        return _finish_section(sec, body, y, top, x0, x1, inner_x0) + ((0, 0),)

    if sec.steps:
        y = _layout_steps(sec, body, y, inner_x0, inner_x1)
        return _finish_section(sec, body, y, top, x0, x1, inner_x0) + ((0, 0),)

    ids = [n[0] for n in sec.nodes]
    meta = {n[0]: n for n in sec.nodes}
    layer, back_ids = _assign_layers(ids, sec.edges)
    rows = sec.layers_hint or _order_layers(layer, ids)

    ax0 = inner_x0 + CHANNEL_W * n_left
    ax1 = inner_x1 - CHANNEL_W * n_right
    avail = ax1 - ax0

    # 行へ展開
    flat_rows = []
    for row in rows:
        flat_rows.extend(_split_row(row, avail))

    # 辺のラベルの有無で層間を決める
    labeled_into = set()
    for src, dst, label, _o in sec.edges:
        if label and id((src, dst, label, _o)) not in back_ids:
            labeled_into.add(dst)

    place, row_of = {}, {}
    for ri, row in enumerate(flat_rows):
        for nid in row:
            row_of[nid] = ri
    for ri, row in enumerate(flat_rows):
        k = len(row)
        gap = NODE_GAP_X if k <= 3 else NODE_GAP_X_TIGHT
        w = (avail - gap * (k - 1)) / k
        sized = []
        for nid in row:
            _i, label, style = meta[nid]
            size, lines = fit(label, w)
            h = max(NODE_MIN_H, NODE_PAD_Y * 2 + len(lines) * (FS[size] + 3))
            if style == "decision":
                h = max(h, 38)
            sized.append((nid, label, style, size, lines, h))
        rh = max(s[5] for s in sized)
        if ri > 0:
            prev_row = flat_rows[ri - 1]
            wants = any(n in labeled_into for n in row)
            y += (sec.gap or (LAYER_GAP_LABELED if wants else LAYER_GAP))
        for i, (nid, label, style, size, lines, h) in enumerate(sized):
            x = ax0 + i * (w + gap)
            ny = y + (rh - h) / 2
            place[nid] = (x, ny, w, h)
            draw = node_hex if style == "decision" else node_box
            body += draw(x, ny, w, h, lines, size, style)
        y += rh

    # 辺。同じ行なら横、素直に下れるなら直交、箱を突き抜けるならチャネルへ逃がす。
    rects = list(place.values())
    deferred = []
    for e in sec.edges:
        src, dst, label, opts = e
        dashed = "dashed" in opts
        color = MUTED if dashed else AXIS
        sx, sy, sw, sh = place[src]
        tx, ty, tw, th = place[dst]

        if row_of[src] == row_of[dst]:
            s = 1 if tx > sx else -1
            cy = max(sy + sh / 2, ty + th / 2)
            body += edge_row(sx + sw if s > 0 else sx, cy,
                             tx if s > 0 else tx + tw, cy, color, dashed)
            if label:
                body += edge_label((sx + sw + tx) / 2 if s > 0 else (sx + tx + tw) / 2,
                                   cy - 9, label, "middle")
            continue

        a, b = sx + sw / 2, tx + tw / 2
        others = [r for r in rects if r not in (place[src], place[dst])]
        forward = id(e) not in back_ids and row_of[dst] > row_of[src]
        if forward and not _hits(_ortho_segments(a, sy + sh, b, ty), others):
            body += edge_ortho(a, sy + sh, b, ty, color, dashed, "both" in opts)
            if label:
                body += edge_label((a + b) / 2, (sy + sh + ty) / 2, label, "middle")
            continue

        deferred.append((e, color, dashed))

    # チャネルは左右どちらにも出せる。出入りの横線が箱を横切らない側を選ぶ。
    # 縦の区間が重ならない辺どうしなら1本のチャネルを共有できる（区間グラフの貪欲彩色）。
    lanes = {"right": [], "left": []}
    for e, color, dashed in deferred:
        src, dst, label, _o = e
        sx, sy, sw, sh = place[src]
        tx, ty, tw, th = place[dst]
        y_a, y_b = sy + sh / 2, ty + th / 2
        others = [r for r in rects if r not in (place[src], place[dst])]

        cost = {}
        for side in ("right", "left"):
            out_x = sx + sw if side == "right" else sx
            in_x = tx + tw if side == "right" else tx
            edge_x = ax1 + 40 if side == "right" else ax0 - 40
            cost[side] = (_hits([(out_x, y_a, edge_x, y_a)], others)
                          + _hits([(in_x, y_b, edge_x, y_b)], others))
        side = "right" if cost["right"] <= cost["left"] else "left"

        lo, hi = min(y_a, y_b), max(y_a, y_b)
        idx = 0
        while (idx < len(lanes[side])
               and any(lo < h and hi > l for l, h in lanes[side][idx])):
            idx += 1
        if idx == len(lanes[side]):
            lanes[side].append([])
        lanes[side][idx].append((lo, hi))

        if side == "right":
            cx = ax1 + CHANNEL_W - 5 + idx * CHANNEL_W
            body += edge_channel(sx + sw, y_a, tx + tw, y_b, cx, color, dashed)
            body += edge_label(cx - 4, (y_a + y_b) / 2, label, "end") if label else []
        else:
            cx = ax0 - CHANNEL_W + 5 - idx * CHANNEL_W
            body += edge_channel(sx, y_a, tx, y_b, cx, color, dashed)
            body += edge_label(cx + 4, (y_a + y_b) / 2, label, "start") if label else []
    n_used = (len(lanes["left"]), len(lanes["right"]))

    return _finish_section(sec, body, y, top, x0, x1, inner_x0) + (n_used,)


def _finish_section(sec, body, y, top, x0, x1, inner_x0):
    if sec.note:
        y += 14
        for ln in sec.note if isinstance(sec.note, (list, tuple)) else [sec.note]:
            body.append(text(_fmt(inner_x0), _fmt(y), ln, "note", MUTED))
            y += 13

    if sec.framed:
        y += 10
        frame = (f'<rect x="{_fmt(x0)}" y="{_fmt(top)}" width="{_fmt(x1-x0)}" '
                 f'height="{_fmt(y-top)}" rx="8" fill="none" stroke="{SOFT}" '
                 f'stroke-width="1"/>')
        body.insert(0, frame)
    return body, y


def _layout_steps(sec, body, y, x0, x1):
    """番号付きの一本道。10段を超える手順を箱と矢印で描くと縦に伸びすぎるので、
    左に番号のレールを立てて詰める。分岐のない列挙にだけ使うこと。"""
    num_w, gap_y = 26, 6
    tx = x0 + num_w + 10
    avail = x1 - tx - 4
    tops = []
    for i, label in enumerate(sec.steps):
        size, lines = fit(label, avail + NODE_PAD_X * 2, ("tick",))
        h = max(24, len(lines) * (FS[size] + 3) + 8)
        tops.append((y, h))
        body.append(f'<rect x="{_fmt(x0)}" y="{_fmt(y)}" width="{num_w}" '
                    f'height="{_fmt(h)}" rx="5" fill="{SHELL}" stroke="{LINE}" '
                    f'stroke-width="1"/>')
        body.append(text(_fmt(x0 + num_w / 2), _fmt(y + h / 2 + FS["note"] / 2 - 1),
                         str(i + 1), "note", INK2, 600, "middle"))
        ly = y + h / 2 - (len(lines) - 1) * (FS[size] + 3) / 2 + FS[size] / 2 - 1.5
        for j, ln in enumerate(lines):
            body.append(text(_fmt(tx), _fmt(ly + j * (FS[size] + 3)), ln, size, INK))
        y += h + gap_y
    # 番号どうしをつなぐレール
    rail_x = x0 + num_w / 2
    for (y0, h0), (y1, _h1) in zip(tops, tops[1:]):
        body.insert(0, _stroke(f"M{_fmt(rail_x)},{_fmt(y0+h0)} L{_fmt(rail_x)},{_fmt(y1)}",
                               AXIS, False, 1.1))
    return y - gap_y


def _layout_chips(sec, body, y, x0, x1):
    """並列に列挙するだけの項目。矢印を引かず、幅に合わせて詰めて折り返す。

    親から辺を引くと折り返した行が意味を持ってしまうので、chips には辺を引かない。
    """
    gap, pad = 8, 11
    avail = x1 - x0
    rows, cur, cur_w = [], [], 0.0
    for label in sec.chips:
        w = est_width(label, FS["tick"]) + pad * 2
        if cur and cur_w + gap + w > avail:
            rows.append((cur, cur_w))
            cur, cur_w = [], 0.0
        cur.append((label, w))
        cur_w += (gap if len(cur) > 1 else 0) + w
    rows.append((cur, cur_w))

    for row, row_w in rows:
        x = x0 + (avail - row_w) / 2
        for label, w in row:
            body += node_box(x, y, w, 26, [label], "tick", sec.chip_style)
            x += w + gap
        y += 26 + gap
    return y - gap


# ---------------------------------------------------------------- 図の組み立て
SECTION_GAP = 16


def figure(uid, title, desc, sections, top=16, bottom=16, footnote=None):
    body = []
    y = top
    for i, sec in enumerate(sections):
        if i:
            y += SECTION_GAP
        part, y = _layout_section(sec, y, PAD, VB_W - PAD)
        body += part
    if footnote:
        y += 16
        for ln in footnote:
            body.append(text(PAD, _fmt(y), ln, "note", MUTED))
            y += 13
    h = round(y + bottom)
    return (
        f'<svg viewBox="0 0 {VB_W} {h}" xmlns="http://www.w3.org/2000/svg" role="img" '
        f'aria-labelledby="{uid}-title {uid}-desc">\n'
        f'<title id="{uid}-title">{title}</title>\n'
        f'<desc id="{uid}-desc">{desc}</desc>\n'
        f"{FONT}\n"
        f'<rect x="0" y="0" width="{VB_W}" height="{h}" rx="8" fill="{SURF}"/>\n'
        + "\n".join(body) + "\n</svg>\n"
    )


def sequence(uid, title, desc, actors, messages, footnote=None):
    """当事者どうしのやり取り。actors は表示名のリスト、messages は
    (送り手, 受け手, ラベル, 返信か) のタプル。

    ライフラインの間隔を先に決めるので、ラベルが長くても図の幅は変わらない。
    そのぶんラベルは自分で短くする必要がある。
    """
    n = len(actors)
    head_h, head_y = 26, 14
    slot = (VB_W - PAD * 2) / n
    xs = [PAD + slot * (i + 0.5) for i in range(n)]
    head_w = min(slot - 10, 110)

    body = []
    for x, name in zip(xs, actors):
        size, lines = fit(name, head_w, ("tick", "note"))
        body += node_box(x - head_w / 2, head_y, head_w, head_h, lines, size, "accent")

    y = head_y + head_h + 24
    step = 34
    for src, dst, label, reply in messages:
        a, b = xs[actors.index(src)], xs[actors.index(dst)]
        color, dashed = (MUTED, True) if reply else (INK2, False)
        s = 1 if b > a else -1
        body.append(text(_fmt((a + b) / 2), _fmt(y - 7), label, "note", INK2, None, "middle"))
        body.append(_stroke(f"M{_fmt(a)},{_fmt(y)} L{_fmt(b-ARROW*s)},{_fmt(y)}",
                            color, dashed))
        body.append(_arrow_head(b, y, "right" if s > 0 else "left", color))
        y += step

    bottom = y - step + 14
    rails = [f'<line x1="{_fmt(x)}" y1="{head_y + head_h}" x2="{_fmt(x)}" '
             f'y2="{_fmt(bottom)}" stroke="{GRID}" stroke-width="1" '
             f'stroke-dasharray="3 4"/>' for x in xs]
    body = rails + body
    y = bottom
    if footnote:
        y += 16
        for ln in footnote:
            body.append(text(PAD, _fmt(y), ln, "note", MUTED))
            y += 13
    h = round(y + 12)
    return (
        f'<svg viewBox="0 0 {VB_W} {h}" xmlns="http://www.w3.org/2000/svg" role="img" '
        f'aria-labelledby="{uid}-title {uid}-desc">\n'
        f'<title id="{uid}-title">{title}</title>\n'
        f'<desc id="{uid}-desc">{desc}</desc>\n'
        f"{FONT}\n"
        f'<rect x="0" y="0" width="{VB_W}" height="{h}" rx="8" fill="{SURF}"/>\n'
        + "\n".join(body) + "\n</svg>\n"
    )


def nested(uid, title, desc, layers, legend=True):
    """入れ子（内包）の図。外側から順に `layers` を受け取る。

    layers: (見出し, 説明, 枠線色, 塗り) のリスト。説明は下の凡例に出す。
    """
    body = []
    top, step_x, step_y, bottom_pad = 16, 15, 30, 14
    n = len(layers)
    outer_w = VB_W - PAD * 2
    outer_h = 34 + (n - 1) * (step_y + bottom_pad)
    for i, (name, _note, col, fill) in enumerate(layers):
        x = PAD + i * step_x
        y = top + i * step_y
        body.append(f'<rect x="{_fmt(x)}" y="{_fmt(y)}" '
                    f'width="{_fmt(outer_w - i*step_x*2)}" '
                    f'height="{_fmt(outer_h - i*(step_y+bottom_pad))}" rx="8" '
                    f'fill="{fill}" stroke="{col}" stroke-width="1.2"/>')
        body.append(text(_fmt(x + 10), _fmt(y + 17), name, "tick", INK, 700))
    y = top + outer_h + 20
    if legend:
        for name, note, col, _fill in layers:
            body.append(f'<rect x="{PAD}" y="{_fmt(y-9)}" width="10" height="10" rx="2" '
                        f'fill="{col}"/>')
            body.append(text(PAD + 16, _fmt(y), f"{name}：{note}", "note", INK2))
            y += 15
    h = round(y + 4)
    return (
        f'<svg viewBox="0 0 {VB_W} {h}" xmlns="http://www.w3.org/2000/svg" role="img" '
        f'aria-labelledby="{uid}-title {uid}-desc">\n'
        f'<title id="{uid}-title">{title}</title>\n'
        f'<desc id="{uid}-desc">{desc}</desc>\n'
        f"{FONT}\n"
        f'<rect x="0" y="0" width="{VB_W}" height="{h}" rx="8" fill="{SURF}"/>\n'
        + "\n".join(body) + "\n</svg>\n"
    )


def write_figure(slug, filename, content):
    d = os.path.join(POSTS_IMG, slug)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, filename)
    with open(path, "w") as f:
        f.write(content)
    print("wrote", os.path.relpath(path, ROOT))
