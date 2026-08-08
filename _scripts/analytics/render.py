"""レポートのMarkdownを組み立てる。日本語記事と英語記事で別ファイルにする。"""

from __future__ import annotations

from analysis import PostMetrics, falling, missed_opportunities, rising

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
        "| 記事 | 公開日 | 閲覧数 | 前期比 | 訪問者 | クリック | 表示 | CTR | 順位 |",
        "| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in rows:
        ratio = "新規" if item.is_new else _ratio(item.pv_ratio)
        lines.append(
            f"| {_post_link(item)} | {item.post.date} | {_num(item.pv)} | {ratio} | "
            f"{_num(item.users)} | {_num(item.clicks)} | {_num(item.impressions)} | "
            f"{_pct(item.ctr)} | {item.position:.1f} |"
        )
    lines.append("")
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


def render(
    lang: str,
    items: list[PostMetrics],
    query_buckets: dict[str, list[dict]],
    channels: list[dict],
    channels_prev: list[dict],
    period: dict,
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
        + _trend_section("伸びている記事", rising(items), "前期比+30%以上の記事がなかった")
        + _trend_section("落ちている記事", falling(items), "前期比-30%以下の記事がなかった")
        + _missed_section(missed_opportunities(items), gsc_has_data)
        + _query_section(query_buckets, gsc_has_data)
        + _table_section(items)
        + _channel_section(channels, channels_prev)
    )
    return "\n".join(head + body)
