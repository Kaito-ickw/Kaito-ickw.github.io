"""レポートのMarkdownを組み立てる。日本語記事と英語記事で別ファイルにする。"""

from __future__ import annotations

from analysis import (
    MIN_SEC_PER_VIEW,
    PostMetrics,
    falling,
    missed_opportunities,
    rising,
    search_visibility_trend,
    source_trend,
)

LANG_LABEL = {"ja": "日本語記事", "en": "英語記事"}


def _escape(text: str) -> str:
    return text.replace("|", "\\|")


def _num(value: float) -> str:
    return f"{int(round(value)):,}"


def _ratio(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value * 100:+.0f}%"


def _pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def _post_link(item: PostMetrics) -> str:
    """タイトルを公開URLへリンクする。記事ファイルはURL末尾のスラッグから引ける。"""
    title = _escape(item.post.title)
    return f"[{title}]({item.url})" if item.url else title


def _summary(items: list[PostMetrics]) -> list[str]:
    pv = sum(i.pv for i in items)
    pv_prev = sum(i.pv_prev for i in items)
    clicks = sum(i.clicks for i in items)
    clicks_prev = sum(i.clicks_prev for i in items)
    impressions = sum(i.impressions for i in items)
    with_data = [i for i in items if i.has_data]

    ratio = ((pv - pv_prev) / pv_prev) if pv_prev else None
    click_ratio = ((clicks - clicks_prev) / clicks_prev) if clicks_prev else None

    lines = [
        "## サマリ",
        "",
        f"- 閲覧数 {_num(pv)}（前期比 {_ratio(ratio)}）",
        f"- 検索クリック {_num(clicks)}（前期比 {_ratio(click_ratio)}） / 検索表示 {_num(impressions)}",
        f"- データのあった記事 {len(with_data)} 本 / 全 {len(items)} 本",
        "",
    ]
    return lines


def _trend_section(title: str, items: list[PostMetrics], note: str) -> list[str]:
    lines = [f"## {title}", ""]
    if not items:
        lines += [f"該当なし（{note}）", ""]
        return lines
    lines += ["| 記事 | 閲覧数 | 前期 | 前期比 |", "| :--- | ---: | ---: | ---: |"]
    for item in items:
        lines.append(
            f"| {_post_link(item)} | {_num(item.pv)} | {_num(item.pv_prev)} | {_ratio(item.pv_ratio)} |"
        )
    lines.append("")
    return lines


NO_GSC_DATA = (
    "Search Console からこの期間のデータが返っていない。"
    "プロパティを登録した直後は、それ以前の実績が遡って入らない。"
)


def _missed_section(items: list[PostMetrics], gsc_has_data: bool) -> list[str]:
    lines = [
        "## 取りこぼしている記事",
        "",
        "検索結果に出ているのにクリックされていない、または追記で順位を上げやすい位置にある記事。",
        "",
    ]
    if not gsc_has_data:
        lines += [NO_GSC_DATA, ""]
        return lines
    if not items:
        lines += ["該当なし。", ""]
        return lines
    lines += [
        "| 記事 | 表示 | クリック | CTR | 平均順位 | 主な流入クエリ |",
        "| :--- | ---: | ---: | ---: | ---: | :--- |",
    ]
    for item in items:
        queries = "、".join(_escape(q.get("query", "")) for q in item.top_queries[:3]) or "—"
        lines.append(
            f"| {_post_link(item)} | {_num(item.impressions)} | {_num(item.clicks)} | "
            f"{_pct(item.ctr)} | {item.position:.1f} | {queries} |"
        )
    lines.append("")
    return lines


def _table_section(items: list[PostMetrics]) -> list[str]:
    rows = sorted(
        [i for i in items if i.has_data], key=lambda i: (i.pv, i.impressions), reverse=True
    )
    lines = [
        "## 記事一覧",
        "",
        "滞在は1閲覧あたりの秒数。ここが0秒台の行は、人が読んだ数として扱わない。",
        "",
        "| 記事 | 公開日 | 閲覧数 | 前期比 | 訪問者 | 滞在 | クリック | 表示 | CTR | 順位 |",
        "| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in rows:
        ratio = "新規" if item.is_new else _ratio(item.pv_ratio)
        stay = f"{item.sec_per_view:.0f}秒" if item.pv else "—"
        if item.is_unread:
            stay += "※"
        lines.append(
            f"| {_post_link(item)} | {item.post.date} | {_num(item.pv)} | {ratio} | "
            f"{_num(item.users)} | {stay} | {_num(item.clicks)} | {_num(item.impressions)} | "
            f"{_pct(item.ctr)} | {item.position:.1f} |"
        )
    lines.append("")
    unread = [i for i in rows if i.is_unread]
    if unread:
        lines += [
            f"※ の {len(unread)} 本は滞在が1閲覧あたり{MIN_SEC_PER_VIEW:.0f}秒未満で、"
            "自動巡回の可能性が高い。伸びた記事としては数えていない。",
            "",
        ]
    silent = [i for i in items if not i.has_data]
    if silent:
        lines += [
            f"データが出なかった記事が {len(silent)} 本ある。"
            "閲覧が少ないとGA4・Search Consoleとも行を返さないことがあるため、"
            "ゼロとは限らない。",
            "",
        ]
    return lines


def _query_section(buckets: dict[str, list[dict]], gsc_has_data: bool) -> list[str]:
    lines = ["## 記事化の候補になる検索クエリ", ""]
    if not gsc_has_data:
        lines += [NO_GSC_DATA, ""]
        return lines

    uncovered = buckets.get("uncovered", [])
    lines += [
        "### どの記事にも紐づいていないクエリ",
        "",
        "検索されて自サイトが表示されているが、受け皿になる記事がない検索語。",
        "",
    ]
    if uncovered:
        lines += ["| クエリ | 表示 | クリック | 平均順位 |", "| :--- | ---: | ---: | ---: |"]
        for row in uncovered:
            lines.append(
                f"| {_escape(row.get('query', ''))} | {_num(row.get('impressions', 0))} | "
                f"{_num(row.get('clicks', 0))} | {row.get('position', 0.0):.1f} |"
            )
    else:
        lines.append("該当なし。")
    lines.append("")

    low_rank = buckets.get("low_rank", [])
    lines += [
        "### 順位が低いまま表示されているクエリ",
        "",
        "記事はあるが順位が振るわない検索語。掘り下げた記事を別に立てる余地がある。",
        "",
    ]
    if low_rank:
        lines += ["| クエリ | 表示 | クリック | 平均順位 |", "| :--- | ---: | ---: | ---: |"]
        for row in low_rank:
            lines.append(
                f"| {_escape(row.get('query', ''))} | {_num(row.get('impressions', 0))} | "
                f"{_num(row.get('clicks', 0))} | {row.get('position', 0.0):.1f} |"
            )
    else:
        lines.append("該当なし。")
    lines.append("")
    return lines


def _channel_section(channels: list[dict], channels_prev: list[dict]) -> list[str]:
    prev = {r.get("sessionDefaultChannelGroup", ""): r.get("sessions", 0.0) for r in channels_prev}
    lines = [
        "## 流入チャネル（サイト全体）",
        "",
        "記事単位ではなくサイト全体の値。日英の内訳は含まない。",
        "",
        "| チャネル | セッション | 前期 | 前期比 |",
        "| :--- | ---: | ---: | ---: |",
    ]
    for row in sorted(channels, key=lambda r: r.get("sessions", 0.0), reverse=True):
        name = row.get("sessionDefaultChannelGroup", "")
        now = row.get("sessions", 0.0)
        before = prev.get(name, 0.0)
        ratio = ((now - before) / before) if before else None
        lines.append(f"| {_escape(name)} | {_num(now)} | {_num(before)} | {_ratio(ratio)} |")
    lines.append("")
    return lines


def _visibility_section(gsc_daily: list[dict], gsc_has_data: bool) -> list[str]:
    """検索での見え方の推移。期間の合計では見えない断落をここで拾う。"""
    lines = [
        "## 検索での見え方の推移（サイト全体・Google）",
        "",
        "記事単位ではなくサイト全体の値。表示回数と平均順位が同じ週にそろって"
        "悪化していたら、記事ではなくサイト全体が検索結果から外れている。",
        "",
    ]
    if not gsc_has_data:
        lines += [NO_GSC_DATA, ""]
        return lines
    weeks = search_visibility_trend(gsc_daily)
    if not weeks:
        lines += ["該当なし。", ""]
        return lines
    lines += ["| 週（月曜） | 表示 | クリック | 平均順位 |", "| :--- | ---: | ---: | ---: |"]
    for week in weeks:
        position = f"{week['position']:.1f}" if week["impressions"] else "—"
        impressions = _num(week["impressions"])
        clicks = _num(week["clicks"])
        lines.append(f"| {week['week']} | {impressions} | {clicks} | {position} |")
    lines.append("")
    return lines


def _source_trend_section(ga_daily_sources: list[dict]) -> list[str]:
    """流入元ごとの週別セッション。どの経路がいつ変わったかを見る。"""
    names, rows = source_trend(ga_daily_sources)
    lines = [
        "## 流入元の推移（サイト全体・週別セッション）",
        "",
        "検索エンジンごとに分けている。片方だけが落ちているなら、"
        "サイトの中身ではなくそのエンジン側での扱いが変わった可能性が高い。",
        "",
    ]
    if not rows:
        lines += ["該当なし。", ""]
        return lines
    header = " | ".join(_escape(name) for name in names)
    lines += [
        f"| 週（月曜） | {header} |",
        "| :--- |" + " ---: |" * len(names),
    ]
    for row in rows:
        cells = " | ".join(_num(row["sessions"].get(name, 0.0)) for name in names)
        lines.append(f"| {row['week']} | {cells} |")
    lines.append("")
    return lines


def render(
    lang: str,
    items: list[PostMetrics],
    query_buckets: dict[str, list[dict]],
    channels: list[dict],
    channels_prev: list[dict],
    period: dict,
    gsc_daily: list[dict] | None = None,
    ga_daily_sources: list[dict] | None = None,
    gsc_has_data: bool = True,
) -> str:
    label = LANG_LABEL.get(lang, lang)
    head = [
        f"# アクセスレポート（{label}）",
        "",
        f"対象期間: {period['current'][0]} 〜 {period['current'][1]}",
        f"比較対象: {period['previous'][0]} 〜 {period['previous'][1]}",
        f"生成日: {period['generated']}",
        "",
        "直近日はデータが確定しないため、期間の終端は数日前に置いている。",
        "",
    ]
    body = (
        _summary(items)
        + _visibility_section(gsc_daily or [], gsc_has_data)
        + _source_trend_section(ga_daily_sources or [])
        + _trend_section("伸びている記事", rising(items), "前期比+30%以上の記事がなかった")
        + _trend_section("落ちている記事", falling(items), "前期比-30%以下の記事がなかった")
        + _missed_section(missed_opportunities(items), gsc_has_data)
        + _query_section(query_buckets, gsc_has_data)
        + _table_section(items)
        + _channel_section(channels, channels_prev)
    )
    return "\n".join(head + body)
