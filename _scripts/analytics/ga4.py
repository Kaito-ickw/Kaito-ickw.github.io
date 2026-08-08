"""GA4 Data API から閲覧数と流入チャネルを取る。"""

from __future__ import annotations

from config import Config, build_credentials

PAGE_ROW_LIMIT = 1000


def _client(config: Config):
    from google.analytics.data_v1beta import BetaAnalyticsDataClient

    return BetaAnalyticsDataClient(credentials=build_credentials(config))


def _run(client, config: Config, dimensions, metrics, start: str, end: str, limit: int):
    from google.analytics.data_v1beta.types import (
        DateRange,
        Dimension,
        Metric,
        RunReportRequest,
    )

    request = RunReportRequest(
        property=config.ga4_property,
        dimensions=[Dimension(name=name) for name in dimensions],
        metrics=[Metric(name=name) for name in metrics],
        date_ranges=[DateRange(start_date=start, end_date=end)],
        limit=limit,
    )
    response = client.run_report(request)

    rows = []
    for row in response.rows:
        record = {
            name: value.value
            for name, value in zip(dimensions, row.dimension_values)
        }
        for name, value in zip(metrics, row.metric_values):
            record[name] = float(value.value or 0)
        rows.append(record)
    return rows


def fetch_pages(config: Config, start: str, end: str) -> list[dict]:
    """ページ単位の閲覧数・訪問者数・エンゲージメント時間。"""
    client = _client(config)
    return _run(
        client,
        config,
        dimensions=["pagePath"],
        metrics=["screenPageViews", "totalUsers", "userEngagementDuration"],
        start=start,
        end=end,
        limit=PAGE_ROW_LIMIT,
    )


def fetch_channels(config: Config, start: str, end: str) -> list[dict]:
    """流入チャネルの内訳。サイト全体の値で、記事単位ではない。"""
    client = _client(config)
    return _run(
        client,
        config,
        dimensions=["sessionDefaultChannelGroup"],
        metrics=["sessions", "totalUsers"],
        start=start,
        end=end,
        limit=50,
    )
