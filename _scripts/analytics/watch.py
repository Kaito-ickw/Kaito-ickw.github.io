#!/usr/bin/env python3
"""レポートを更新し、直前のスナップショットから変わった点だけを短く出す。

    python3 _scripts/analytics/watch.py
    python3 _scripts/analytics/watch.py --no-fetch

fetch.py と同じ取得を行ってレポートを更新したうえで、`.analytics/` に残っている
直前のスナップショットと比べ、判断に効く変化だけを標準出力へ書く。定期実行して
差分だけを読むための入口で、数値そのものは latest-ja.md を見る。

進捗と失敗は標準エラーへ出す。標準出力は差分だけなので、cron から
そのままファイルへ落として読める。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import analysis  # noqa: E402
import fetch  # noqa: E402
from config import OUTPUT_ROOT, ConfigError, load_config  # noqa: E402
from posts import load_posts  # noqa: E402

# --- 変化として報告する基準 -----------------------------------------------

IMPRESSION_RATIO = 0.3   # 週次の検索表示がこれ以上動いたら report する
POSITION_DELTA = 3.0     # 平均順位がこれだけ動いたら report する（位）
SESSION_RATIO = 0.3      # 検索エンジン別の週次セッションの変化幅
MIN_SESSIONS = 5         # これ未満の流入元は比率が暴れるので見ない
# 前回になかったクエリを載せる最低表示回数。レポートで記事化候補に挙げる基準へそろえる。
# 表示1〜2回のクエリは毎回入れ替わるため、下げると差分がノイズで埋まる。
NEW_QUERY_IMPRESSIONS = analysis.MIN_IMPRESSIONS_UNCOVERED
MAX_POSTS = 3            # 伸び・落ちで並べる記事数
MAX_SOURCES = 3          # 流入元で並べる行数
MAX_QUERIES = 4          # 新しいクエリで並べる行数
TITLE_WIDTH = 34         # 記事タイトルはこの長さで打ち切る

SNAPSHOT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def log(message: str) -> None:
    print(message, file=sys.stderr)


# --- スナップショットの読み書き -------------------------------------------


def snapshots() -> list[Path]:
    """生データの残っている出力ディレクトリを古い順に返す。"""
    if not OUTPUT_ROOT.exists():
        return []
    found = [
        path
        for path in OUTPUT_ROOT.iterdir()
        if path.is_dir() and SNAPSHOT_RE.match(path.name) and (path / "raw").is_dir()
    ]
    return sorted(found, key=lambda path: path.name)


def load_raw(snapshot: Path) -> dict:
    """raw/*.json をまとめて読む。取り始める前の項目は欠けているので、無ければ空。"""
    raw: dict[str, list[dict]] = {}
    for path in sorted((snapshot / "raw").glob("*.json")):
        try:
            raw[path.stem] = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            raw[path.stem] = []
    return raw


# --- 週の扱い -------------------------------------------------------------


def _to_date(value: str) -> date | None:
    """GA4形式(20260901)・GSC形式(2026-09-01)のどちらも受ける。"""
    text = str(value).replace("-", "")
    if len(text) != 8 or not text.isdigit():
        return None
    return date(int(text[:4]), int(text[4:6]), int(text[6:]))


def _last_day(rows: list[dict]) -> date | None:
    days = [d for d in (_to_date(row.get("date", "")) for row in rows) if d]
    return max(days) if days else None


def _complete(weeks: list[dict], end: date | None) -> list[dict]:
    """7日そろっている週だけを残す。取得範囲の端にかかる週は比較に使えない。"""
    if end is None:
        return []
    kept = []
    for week in weeks:
        start = _to_date(week["week"])
        if start and start + timedelta(days=6) <= end:
            kept.append(week)
    return kept


def _before(weeks: list[dict], cutoff: date, fallback: list[dict]) -> dict | None:
    """前回実行の時点で見えていた週。

    直近84日分は毎回取り直しているので、通常は今回のデータの中から選べる。
    前回の実行が84日より前なら、その回のスナップショットから取る。
    """
    picked = [
        week
        for week in weeks
        if (start := _to_date(week["week"])) and start + timedelta(days=6) <= cutoff
    ]
    if picked:
        return picked[-1]
    return fallback[-1] if fallback else None


# --- 表示 -----------------------------------------------------------------


def _num(value: float) -> str:
    return f"{int(round(value)):,}"


def _ratio(now: float, before: float) -> str:
    if before <= 0:
        return "新規"
    return f"{(now - before) / before * 100:+.0f}%"


def _moved(now: float, before: float, ratio: float) -> bool:
    if before <= 0:
        return now > 0
    return abs(now - before) / before >= ratio


def _title(text: str) -> str:
    return text if len(text) <= TITLE_WIDTH else text[: TITLE_WIDTH - 1] + "…"


def _week_label(week: dict) -> str:
    return f"{week['week']}週"


# --- 項目ごとの比較 -------------------------------------------------------


def visibility_lines(current: dict, previous: dict, cutoff: date) -> list[str]:
    """Google検索での見え方。崩落と回復を拾うための主指標。"""
    daily = current.get("gsc-daily", [])
    weeks = _complete(analysis.search_visibility_trend(daily), _last_day(daily))
    if len(weeks) < 1:
        return []
    now = weeks[-1]
    prev_daily = previous.get("gsc-daily", [])
    fallback = _complete(
        analysis.search_visibility_trend(prev_daily), _last_day(prev_daily)
    )
    before = _before(weeks[:-1], cutoff, fallback)
    if before is None or before["week"] == now["week"]:
        return []

    span = f"{_week_label(before)} → {_week_label(now)}"
    lines = []
    if _moved(now["impressions"], before["impressions"], IMPRESSION_RATIO):
        lines.append(
            f"検索表示（週次） {_num(before['impressions'])} → {_num(now['impressions'])}"
            f"（{_ratio(now['impressions'], before['impressions'])}） {span}"
        )
    if before["impressions"] and now["impressions"]:
        delta = now["position"] - before["position"]
        if abs(delta) >= POSITION_DELTA:
            direction = "悪化" if delta > 0 else "改善"
            lines.append(
                f"平均順位 {before['position']:.1f} → {now['position']:.1f}"
                f"（{abs(delta):.1f}位{direction}） {span}"
            )
    return lines


def source_lines(current: dict, previous: dict, cutoff: date) -> list[str]:
    """検索エンジン別の週次セッション。片方だけ落ちたのかを見る。"""
    daily = current.get("ga4-daily-sources", [])
    names, rows = analysis.source_trend(daily)
    weeks = _complete(rows, _last_day(daily))
    if len(weeks) < 1:
        return []
    now = weeks[-1]
    prev_daily = previous.get("ga4-daily-sources", [])
    _, prev_rows = analysis.source_trend(prev_daily)
    fallback = _complete(prev_rows, _last_day(prev_daily))
    before = _before(weeks[:-1], cutoff, fallback)
    if before is None or before["week"] == now["week"]:
        return []

    span = f"{_week_label(before)} → {_week_label(now)}"
    changed = []
    for name in names:
        after = now["sessions"].get(name, 0.0)
        first = before["sessions"].get(name, 0.0)
        if max(after, first) < MIN_SESSIONS:
            continue
        if _moved(after, first, SESSION_RATIO):
            changed.append((abs(after - first), name, first, after))
    changed.sort(reverse=True)
    return [
        f"{name} セッション（週次） {_num(first)} → {_num(after)}"
        f"（{_ratio(after, first)}） {span}"
        for _, name, first, after in changed[:MAX_SOURCES]
    ]


def _post_metrics(raw: dict, posts: dict) -> list:
    return list(
        analysis.build_post_metrics(
            posts,
            raw.get("ga4-pages", []),
            raw.get("ga4-pages-previous", []),
            raw.get("gsc-pages", []),
            raw.get("gsc-pages-previous", []),
            raw.get("gsc-page-queries", []),
        ).values()
    )


def post_lines(current: dict, previous: dict) -> list[str]:
    """伸び・落ちの一覧へ新しく入った記事。滞在の短い行は analysis 側で除いてある。"""
    posts = load_posts()
    now_items = _post_metrics(current, posts)
    before_items = _post_metrics(previous, posts)

    lines = []
    for label, pick in (("伸びた記事", analysis.rising), ("落ちた記事", analysis.falling)):
        known = {item.post.key for item in pick(before_items)}
        added = [item for item in pick(now_items) if item.post.key not in known]
        for item in added[:MAX_POSTS]:
            ratio = "新規" if item.is_new else _ratio(item.pv, item.pv_prev)
            lines.append(
                f"{label}: {_title(item.post.title)}"
                f"（閲覧 {_num(item.pv)}、前期比 {ratio}）"
            )
    return lines


def query_lines(current: dict, previous: dict) -> list[str]:
    """前回のスナップショットになかった検索クエリのうち、表示回数の多いもの。"""
    known = {row.get("query", "") for row in previous.get("gsc-queries", [])}
    fresh = [
        row
        for row in current.get("gsc-queries", [])
        if row.get("query", "") not in known
        and row.get("impressions", 0) >= NEW_QUERY_IMPRESSIONS
    ]
    fresh.sort(key=lambda row: row.get("impressions", 0), reverse=True)
    return [
        f"新しい検索クエリ「{row.get('query', '')}」"
        f"（表示 {_num(row.get('impressions', 0))}、順位 {row.get('position', 0.0):.1f}）"
        for row in fresh[:MAX_QUERIES]
    ]


def diff_lines(current: dict, previous: dict, cutoff: date) -> list[str]:
    return (
        visibility_lines(current, previous, cutoff)
        + source_lines(current, previous, cutoff)
        + post_lines(current, previous)
        + query_lines(current, previous)
    )


# --- 実行 -----------------------------------------------------------------


def refresh(days: int, end_offset: int) -> Path | None:
    """fetch.py と同じ取得を行い、書き出し先のディレクトリを返す。"""
    try:
        config = load_config()
    except ConfigError as error:
        log(f"設定エラー\n{error}")
        return None

    period = fetch.build_periods(days, end_offset, date.today())
    log(f"対象期間 {period['current'][0]} 〜 {period['current'][1]}")
    try:
        raw = fetch.collect(config, period, log=log)
    except Exception as error:  # 認証・権限まわりの失敗を分かりやすく出す
        log(f"取得に失敗した: {error}\n")
        log(fetch.FETCH_ERROR_HINT)
        return None

    if not raw["gsc-pages"] and not raw["gsc-queries"]:
        log(fetch.NO_GSC_DATA_HINT)

    out_dir, _ = fetch.write_reports(config, period, raw)
    log(f"レポートを更新した: {OUTPUT_ROOT}/latest-ja.md")
    return out_dir


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=fetch.DEFAULT_DAYS, help="集計する日数")
    parser.add_argument(
        "--end-offset",
        type=int,
        default=fetch.DEFAULT_END_OFFSET,
        help="何日前を期間の終端にするか",
    )
    parser.add_argument(
        "--no-fetch",
        action="store_true",
        help="取得せず、すでにある直近2回のスナップショットだけを比べる",
    )
    args = parser.parse_args()

    if args.no_fetch:
        found = snapshots()
        current_dir = found[-1] if found else None
    else:
        current_dir = refresh(args.days, args.end_offset)
    if current_dir is None:
        log("比較できるスナップショットがない。")
        return 1

    older = [path for path in snapshots() if path.name < current_dir.name]
    if not older:
        print(
            f"比較できる直前のスナップショットがない（今回分 {current_dir.name} のみ）。"
            "次回の実行から差分を出す。"
        )
        return 0

    previous_dir = older[-1]
    cutoff = date.fromisoformat(previous_dir.name) - timedelta(days=args.end_offset)
    lines = diff_lines(load_raw(current_dir), load_raw(previous_dir), cutoff)

    if not lines:
        print(f"前回 {previous_dir.name} と比べて大きな変化なし。")
        return 0

    print(f"前回 {previous_dir.name} との比較（今回 {current_dir.name}）")
    for line in lines:
        print(f"- {line}")
    print(f"詳細は {OUTPUT_ROOT}/latest-ja.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
