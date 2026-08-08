"""Search Console から検索流入を取る。

GA4では取れない「どんな検索語で来たか」「何位に出ているか」がここで手に入る。
ネタ選びに効くのは主にこちら。
"""

from __future__ import annotations

from config import Config, build_credentials


def _service(config: Config):
    from googleapiclient.discovery import build

    return build(
        "searchconsole", "v1", credentials=build_credentials(config), cache_discovery=False
    )


def _query(config: Config, dimensions: list[str], start: str, end: str, limit: int) -> list[dict]:
    service = _service(config)
    body = {
        "startDate": start,
        "endDate": end,
        "dimensions": dimensions,
        "type": "web",
        "rowLimit": limit,
    }
    response = (
        service.searchanalytics().query(siteUrl=config.gsc_site_url, body=body).execute()
    )

    rows = []
    for row in response.get("rows", []):
        record = dict(zip(dimensions, row.get("keys", [])))
        record["clicks"] = row.get("clicks", 0)
        record["impressions"] = row.get("impressions", 0)
        record["ctr"] = row.get("ctr", 0.0)
        record["position"] = row.get("position", 0.0)
        rows.append(record)
    return rows


def fetch_pages(config: Config, start: str, end: str) -> list[dict]:
    return _query(config, ["page"], start, end, limit=1000)


def fetch_queries(config: Config, start: str, end: str) -> list[dict]:
    return _query(config, ["query"], start, end, limit=500)


def fetch_page_queries(config: Config, start: str, end: str) -> list[dict]:
    """記事ごとの流入クエリ。どのクエリが既存記事で拾えているかの判定に使う。"""
    return _query(config, ["page", "query"], start, end, limit=5000)
