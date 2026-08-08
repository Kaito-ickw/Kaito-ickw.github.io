#!/usr/bin/env python3
"""GA4とSearch Consoleからデータを取り、編集判断用のレポートを生成する。

    python3 _scripts/analytics/fetch.py
    python3 _scripts/analytics/fetch.py --days 90

出力は .analytics/ 以下。このディレクトリは .gitignore 済みで、
リポジトリへコミットされない。
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import analysis  # noqa: E402
import ga4  # noqa: E402
import gsc  # noqa: E402
import render  # noqa: E402
from config import OUTPUT_ROOT, ConfigError, load_config  # noqa: E402
from posts import load_posts  # noqa: E402

# GA4もSearch Consoleも直近数日のデータは確定しない。既定でこの日数だけ遡る。
DEFAULT_END_OFFSET = 3
DEFAULT_DAYS = 28


def build_periods(days: int, end_offset: int, today: date) -> dict:
    end = today - timedelta(days=end_offset)
    start = end - timedelta(days=days - 1)
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=days - 1)
    return {
        "current": (start.isoformat(), end.isoformat()),
        "previous": (prev_start.isoformat(), prev_end.isoformat()),
        "generated": today.isoformat(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS, help="集計する日数")
    parser.add_argument(
        "--end-offset",
        type=int,
        default=DEFAULT_END_OFFSET,
        help="何日前を期間の終端にするか",
    )
    args = parser.parse_args()

    try:
        config = load_config()
    except ConfigError as error:
        print(f"設定エラー\n{error}", file=sys.stderr)
        return 1

    period = build_periods(args.days, args.end_offset, date.today())
    now_start, now_end = period["current"]
    prev_start, prev_end = period["previous"]

    print(f"対象期間 {now_start} 〜 {now_end}（比較: {prev_start} 〜 {prev_end}）")

    try:
        print("GA4 を取得中...")
        ga_pages = ga4.fetch_pages(config, now_start, now_end)
        ga_pages_prev = ga4.fetch_pages(config, prev_start, prev_end)
        ga_channels = ga4.fetch_channels(config, now_start, now_end)
        ga_channels_prev = ga4.fetch_channels(config, prev_start, prev_end)

        print("Search Console を取得中...")
        gsc_pages = gsc.fetch_pages(config, now_start, now_end)
        gsc_pages_prev = gsc.fetch_pages(config, prev_start, prev_end)
        gsc_queries = gsc.fetch_queries(config, now_start, now_end)
        gsc_page_queries = gsc.fetch_page_queries(config, now_start, now_end)
    except Exception as error:  # 認証・権限まわりの失敗を分かりやすく出す
        print(f"\n取得に失敗した: {error}\n", file=sys.stderr)
        print(
            "権限エラー（403）の場合、サービスアカウントのメールアドレスが\n"
            "  - GA4「プロパティのアクセス管理」に閲覧者として\n"
            "  - Search Console「ユーザーと権限」に制限付きとして\n"
            "それぞれ登録されているか確認する。APIの有効化だけでは足りない。",
            file=sys.stderr,
        )
        return 1

    if not gsc_pages and not gsc_queries:
        print(
            "\n注意: Search Console がこの期間のデータを返していない。\n"
            "  プロパティを登録した直後は、それ以前の実績が遡って入らない。\n"
            "  Search Consoleの画面には実績が出ているのにここが空なら、権限が足りていない。",
            file=sys.stderr,
        )

    posts = load_posts()
    site_url = config.gsc_site_url
    if site_url.startswith("sc-domain:"):
        site_url = "https://" + site_url.split(":", 1)[1]
    metrics = analysis.build_post_metrics(
        posts,
        ga_pages,
        ga_pages_prev,
        gsc_pages,
        gsc_pages_prev,
        gsc_page_queries,
        site_url=site_url,
    )
    grouped = analysis.split_by_lang(metrics)
    query_buckets = analysis.query_candidates(gsc_queries, gsc_page_queries, posts)

    out_dir = OUTPUT_ROOT / period["generated"]
    raw_dir = out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    raw = {
        "ga4-pages": ga_pages,
        "ga4-pages-previous": ga_pages_prev,
        "ga4-channels": ga_channels,
        "ga4-channels-previous": ga_channels_prev,
        "gsc-pages": gsc_pages,
        "gsc-pages-previous": gsc_pages_prev,
        "gsc-queries": gsc_queries,
        "gsc-page-queries": gsc_page_queries,
    }
    for name, rows in raw.items():
        (raw_dir / f"{name}.json").write_text(
            json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    written = []
    for lang in ("ja", "en"):
        items = grouped.get(lang, [])
        if not items:
            continue
        text = render.render(
            lang,
            items,
            query_buckets.get(lang, {}),
            ga_channels,
            ga_channels_prev,
            period,
            gsc_has_data=bool(gsc_pages or gsc_queries),
        )
        path = out_dir / f"report-{lang}.md"
        path.write_text(text, encoding="utf-8")
        shutil.copyfile(path, OUTPUT_ROOT / f"latest-{lang}.md")
        written.append(path)

    print("\n出力:")
    for path in written:
        print(f"  {path}")
    print(f"  {OUTPUT_ROOT}/latest-ja.md（最新版のコピー）")
    print(f"  {raw_dir}/*.json（再集計用の生データ）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
