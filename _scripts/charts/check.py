"""生成したSVGの当たり判定チェック。

この環境ではSVGをラスタライズできないので、代わりに座標と推定文字幅から
「viewBoxからのはみ出し」と「同じ高さに置かれたテキスト同士の重なり」を機械的に見る。
目視確認の代わりにはならないが、崩れの大半はここで拾える。

    python3 _scripts/charts/check.py
"""

import glob
import os
import re
import sys

from common import FS, POSTS_IMG, VB_W

# 文字幅の概算（font-size に対する比率）
W_WIDE = 1.0    # 日本語・全角
W_NARROW = 0.55  # 英数字・記号

# モバイル/デスクトップでの実表示幅（_sass/misc/chart.scss の max-width と本文幅から）
MOBILE_PX = 330
DESKTOP_PX = 560

TEXT_RE = re.compile(
    r'<text x="([-\d.]+)" y="([-\d.]+)" font-size="([\d.]+)"'
    r'(?: font-weight="\d+")?(?: text-anchor="(\w+)")?[^>]*>([^<]*)</text>'
)


def est_width(s, size):
    w = 0.0
    for ch in s:
        w += W_WIDE if ord(ch) > 0x2E80 else W_NARROW
    return w * size


def check(path):
    s = open(path).read()
    m = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', s)
    W, H = float(m.group(1)), float(m.group(2))
    name = os.path.basename(path)
    problems = []

    if W != VB_W:
        problems.append(f"viewBox幅が {W}（{VB_W} に揃える）")

    # 図形のはみ出し
    xs = [float(v) for v in re.findall(r'[ ]x[12]?="([-\d.]+)"', s) + re.findall(r'cx="([-\d.]+)"', s)]
    ys = [float(v) for v in re.findall(r'[ ]y[12]?="([-\d.]+)"', s) + re.findall(r'cy="([-\d.]+)"', s)]
    if min(xs) < 0 or max(xs) > W:
        problems.append(f"x座標が範囲外: {min(xs)}〜{max(xs)}（0〜{W}）")
    if min(ys) < 0 or max(ys) > H:
        problems.append(f"y座標が範囲外: {min(ys)}〜{max(ys)}（0〜{H}）")

    # テキストのはみ出しと重なり
    spans = []
    for x, y, size, anchor, body in TEXT_RE.findall(s):
        x, y, size = float(x), float(y), float(size)
        w = est_width(body, size)
        if anchor == "middle":
            x0 = x - w / 2
        elif anchor == "end":
            x0 = x - w
        else:
            x0 = x
        x1 = x0 + w
        if x0 < -1 or x1 > W + 1:
            problems.append(f'文字がはみ出し y={y:.0f} "{body[:24]}" → {x0:.0f}〜{x1:.0f}')
        spans.append((y, x0, x1, body, size))

    for i, (y1, a0, a1, t1, s1) in enumerate(spans):
        for y2, b0, b1, t2, s2 in spans[i + 1:]:
            if abs(y1 - y2) < max(s1, s2) * 0.8 and a0 < b1 - 1 and b0 < a1 - 1:
                problems.append(f'文字が重なり y≈{y1:.0f} "{t1[:16]}" × "{t2[:16]}"')

    # 実表示での文字サイズ
    sizes = {float(v) for v in re.findall(r'font-size="([\d.]+)"', s)}
    smallest = min(sizes)
    mobile = smallest * MOBILE_PX / W
    if mobile < 8.0:
        problems.append(f"最小フォントがモバイルで {mobile:.1f}px（8px未満）")

    print(f"{'NG ' if problems else 'ok '} {name:34s} {int(W)}x{int(H)}  "
          f"最小文字 モバイル{smallest * MOBILE_PX / W:.1f}px / PC{smallest * DESKTOP_PX / W:.1f}px")
    for p in problems:
        print(f"      - {p}")
    return len(problems)


if __name__ == "__main__":
    targets = sorted(glob.glob(os.path.join(POSTS_IMG, "*", "*.svg")))
    total = sum(check(t) for t in targets)
    print(f"\n{len(targets)}枚を確認。指摘 {total}件。")
    print(f"想定表示幅: モバイル {MOBILE_PX}px / デスクトップ {DESKTOP_PX}px（.chart の max-width）")
    sys.exit(1 if total else 0)
