"""取得した生データを、編集判断に使える形へ組み替える。

しきい値はここへ集約する。レポートの見た目を変えたいときは render.py、
「どれを候補として挙げるか」を変えたいときはこのファイルを触る。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from posts import Post, url_to_key

# --- 候補として挙げる基準 -------------------------------------------------

MIN_PV_FOR_TREND = 5         # 前期比を見るのに必要な最低閲覧数
TREND_RATIO = 0.3            # ±30%を超えた変化を「伸び／落ち」とする
MIN_IMPRESSIONS_MISSED = 100  # 取りこぼし候補とみなす最低表示回数
LOW_CTR = 0.02               # クリック率2%未満はタイトル改訂の候補
WINNABLE_POSITION = (8.0, 25.0)  # この順位帯は追記で上げやすい
MIN_IMPRESSIONS_UNCOVERED = 10   # 未カバークエリとして挙げる最低表示回数
MIN_IMPRESSIONS_LOWRANK = 30     # 低順位クエリとして挙げる最低表示回数
LOW_RANK_POSITION = 20.0
TOP_QUERIES_PER_POST = 5

JAPANESE_RE = re.compile(r"[ぁ-んァ-ヴ一-龥]")


@dataclass
class PostMetrics:
    post: Post
    url: str = ""
    pv: float = 0.0
    pv_prev: float = 0.0
    users: float = 0.0
    engagement_sec: float = 0.0
    clicks: float = 0.0
    clicks_prev: float = 0.0
    impressions: float = 0.0
    ctr: float = 0.0
    position: float = 0.0
    top_queries: list[dict] = field(default_factory=list)

    @property
    def pv_ratio(self) -> float | None:
        if self.pv_prev <= 0:
            return None
        return (self.pv - self.pv_prev) / self.pv_prev

    @property
    def has_data(self) -> bool:
        return self.pv > 0 or self.impressions > 0

    @property
    def is_new(self) -> bool:
        """前期にはまだ公開されていなかった記事。前期比の対象から外す。"""
        return self.pv_prev == 0 and self.pv > 0


def _index(rows: list[dict], url_field: str) -> dict[str, dict]:
    merged: dict[str, dict] = {}
    for row in rows:
        raw = row.get(url_field, "")
        key = url_to_key(raw)
        if key is None:
            continue
        current = merged.setdefault(key, {"_url": raw})
        for name, value in row.items():
            if isinstance(value, (int, float)):
                current[name] = current.get(name, 0.0) + value
    return merged


def _absolute(url: str, site_url: str) -> str:
    if url.startswith("http"):
        return url
    return site_url.rstrip("/") + url


def build_post_metrics(
    posts: dict[str, Post],
    ga_pages: list[dict],
    ga_pages_prev: list[dict],
    gsc_pages: list[dict],
    gsc_pages_prev: list[dict],
    gsc_page_queries: list[dict],
    site_url: str = "https://waka-ds.com",
) -> dict[str, PostMetrics]:
    ga_now = _index(ga_pages, "pagePath")
    ga_prev = _index(ga_pages_prev, "pagePath")
    gsc_now = _index(gsc_pages, "page")
    gsc_prev = _index(gsc_pages_prev, "page")

    metrics = {key: PostMetrics(post=post) for key, post in posts.items()}

    for key, values in ga_now.items():
        if key in metrics:
            metrics[key].url = _absolute(values.get("_url", ""), site_url)
            metrics[key].pv = values.get("screenPageViews", 0.0)
            metrics[key].users = values.get("totalUsers", 0.0)
            metrics[key].engagement_sec = values.get("userEngagementDuration", 0.0)
    for key, values in ga_prev.items():
        if key in metrics:
            metrics[key].pv_prev = values.get("screenPageViews", 0.0)

    for key, values in gsc_now.items():
        if key not in metrics:
            continue
        item = metrics[key]
        item.url = item.url or _absolute(values.get("_url", ""), site_url)
        item.clicks = values.get("clicks", 0.0)
        item.impressions = values.get("impressions", 0.0)
        item.ctr = item.clicks / item.impressions if item.impressions else 0.0
        item.position = values.get("position", 0.0)
    for key, values in gsc_prev.items():
        if key in metrics:
            metrics[key].clicks_prev = values.get("clicks", 0.0)

    for row in gsc_page_queries:
        key = url_to_key(row.get("page", ""))
        if key in metrics:
            metrics[key].top_queries.append(row)
    for item in metrics.values():
        item.top_queries.sort(key=lambda r: r.get("impressions", 0), reverse=True)
        item.top_queries = item.top_queries[:TOP_QUERIES_PER_POST]

    return metrics


def split_by_lang(metrics: dict[str, PostMetrics]) -> dict[str, list[PostMetrics]]:
    grouped: dict[str, list[PostMetrics]] = {"ja": [], "en": []}
    for item in metrics.values():
        grouped.setdefault(item.post.lang, []).append(item)
    return grouped


# --- セクションごとの抽出 -------------------------------------------------


def rising(items: list[PostMetrics]) -> list[PostMetrics]:
    picked = [
        i
        for i in items
        if i.pv >= MIN_PV_FOR_TREND and i.pv_ratio is not None and i.pv_ratio >= TREND_RATIO
    ]
    return sorted(picked, key=lambda i: i.pv_ratio or 0, reverse=True)[:10]


def falling(items: list[PostMetrics]) -> list[PostMetrics]:
    picked = [
        i
        for i in items
        if i.pv_prev >= MIN_PV_FOR_TREND
        and i.pv_ratio is not None
        and i.pv_ratio <= -TREND_RATIO
    ]
    return sorted(picked, key=lambda i: i.pv_ratio or 0)[:10]


def missed_opportunities(items: list[PostMetrics]) -> list[PostMetrics]:
    """検索に出ているのに取りきれていない記事。タイトル改訂・追記の候補。"""
    low, high = WINNABLE_POSITION
    picked = [
        i
        for i in items
        if i.impressions >= MIN_IMPRESSIONS_MISSED
        and (i.ctr < LOW_CTR or low <= i.position <= high)
    ]
    return sorted(picked, key=lambda i: i.impressions, reverse=True)[:15]


def _query_lang(query: str) -> str:
    return "ja" if JAPANESE_RE.search(query) else "en"


def query_candidates(
    gsc_queries: list[dict],
    gsc_page_queries: list[dict],
    posts: dict[str, Post],
) -> dict[str, dict[str, list[dict]]]:
    """記事化の候補になるクエリを言語別に2種類へ分ける。

    uncovered  … どの記事にも紐づいていない。トップやカテゴリ一覧で拾っている検索語
    low_rank   … 記事はあるが順位が低く、表示されるだけで取れていない検索語
    """
    covered: set[str] = set()
    for row in gsc_page_queries:
        key = url_to_key(row.get("page", ""))
        if key in posts:
            covered.add(row.get("query", ""))

    result: dict[str, dict[str, list[dict]]] = {
        "ja": {"uncovered": [], "low_rank": []},
        "en": {"uncovered": [], "low_rank": []},
    }
    for row in gsc_queries:
        query = row.get("query", "")
        lang = _query_lang(query)
        impressions = row.get("impressions", 0)
        if query not in covered and impressions >= MIN_IMPRESSIONS_UNCOVERED:
            result[lang]["uncovered"].append(row)
        elif (
            impressions >= MIN_IMPRESSIONS_LOWRANK
            and row.get("position", 0.0) > LOW_RANK_POSITION
        ):
            result[lang]["low_rank"].append(row)

    for lang in result:
        for bucket in result[lang]:
            result[lang][bucket].sort(key=lambda r: r.get("impressions", 0), reverse=True)
            result[lang][bucket] = result[lang][bucket][:25]
    return result
