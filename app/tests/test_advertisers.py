from datetime import date, timedelta
from typing import Any

from fastapi.testclient import TestClient

from app.api import deps
from app.db.base import get_supabase
from app.main import app


class FakeResponse:
    def __init__(self, data, count: int | None = None):
        self.data = data
        self.count = count


class FakeTableQuery:
    def __init__(self, table_name: str, storage: dict[str, list[dict]]):
        self.table_name = table_name
        self.storage = storage
        self.filters: list = []
        self.orders: list[tuple[str, bool]] = []
        self.limit_value: int | None = None
        self.select_count: str | None = None
        self.head = False

    def select(self, *_args, **kwargs):
        self.select_count = kwargs.get("count")
        self.head = bool(kwargs.get("head", False))
        return self

    def eq(self, field, value):
        self.filters.append(lambda row: row.get(field) == value)
        return self

    def in_(self, field, values):
        allowed = set(values)
        self.filters.append(lambda row: row.get(field) in allowed)
        return self

    def order(self, field: str, desc: bool = False, **_kwargs):
        self.orders.append((field, desc))
        return self

    def limit(self, count: int):
        self.limit_value = count
        return self

    def _sort_rows(self, rows: list[dict], field: str, desc: bool) -> list[dict]:
        non_null_rows = [row for row in rows if row.get(field) is not None]
        null_rows = [row for row in rows if row.get(field) is None]
        non_null_rows.sort(key=lambda row: row.get(field), reverse=desc)
        return non_null_rows + null_rows

    def execute(self):
        rows = [
            row.copy()
            for row in self.storage.get(self.table_name, [])
            if all(f(row) for f in self.filters)
        ]
        total_count = len(rows)

        for field, desc in reversed(self.orders):
            rows = self._sort_rows(rows, field, desc)

        if self.limit_value is not None:
            rows = rows[: self.limit_value]

        if self.head:
            return FakeResponse([], count=total_count if self.select_count else None)

        return FakeResponse(rows, count=total_count if self.select_count else None)


class FakeSupabaseClient:
    def __init__(self, storage: dict[str, list[dict]]):
        self.storage = storage

    def table(self, table_name: str):
        return FakeTableQuery(table_name, self.storage)


def _override_current_user():
    return {"id": "user-1", "email": "user@example.com"}


def _build_storage(*, include_baseline: bool = True) -> dict[str, list[dict]]:
    today = date.today()
    snapshot_date = today
    baseline_date = today - timedelta(days=30)
    old_snapshot = today - timedelta(days=1)

    adv_1 = "2e63db9e-13f7-4204-b8b6-a394f40ca83a"
    adv_2 = "a18b18bb-0000-4000-8000-000000000002"
    adv_3 = "a18b18bb-0000-4000-8000-000000000003"
    adv_4 = "a18b18bb-0000-4000-8000-000000000004"
    crypto_id = "ind-crypto"
    tech_id = "ind-tech"
    gaming_id = "ind-gaming"

    metrics = [
        {
            "advertiser_id": adv_1,
            "metric_date": snapshot_date.isoformat(),
            "estimated_spend": 2500000.0,
            "total_ads": 4500,
            "active_creatives": 156,
            "channels_used": 1200,
            "avg_engagement_rate": 4.2,
            "trend_percent": 15.3,
        },
        {
            "advertiser_id": adv_2,
            "metric_date": snapshot_date.isoformat(),
            "estimated_spend": 1800000.0,
            "total_ads": 3900,
            "active_creatives": 89,
            "channels_used": 2100,
            "avg_engagement_rate": 5.8,
            "trend_percent": 22.1,
        },
        {
            "advertiser_id": adv_3,
            "metric_date": snapshot_date.isoformat(),
            "estimated_spend": 1500000.0,
            "total_ads": 3200,
            "active_creatives": 234,
            "channels_used": 890,
            "avg_engagement_rate": 3.1,
            "trend_percent": -5.2,
        },
        {
            "advertiser_id": adv_4,
            "metric_date": old_snapshot.isoformat(),
            "estimated_spend": 1200000.0,
            "total_ads": 3000,
            "active_creatives": 112,
            "channels_used": 756,
            "avg_engagement_rate": 3.9,
            "trend_percent": 8.7,
        },
    ]
    if include_baseline:
        metrics.extend(
            [
                {
                    "advertiser_id": adv_1,
                    "metric_date": baseline_date.isoformat(),
                    "estimated_spend": 2000000.0,
                    "total_ads": 4000,
                    "active_creatives": 140,
                    "channels_used": 1000,
                    "avg_engagement_rate": 4.0,
                    "trend_percent": 10.0,
                },
                {
                    "advertiser_id": adv_2,
                    "metric_date": baseline_date.isoformat(),
                    "estimated_spend": 2000000.0,
                    "total_ads": 4050,
                    "active_creatives": 98,
                    "channels_used": 2000,
                    "avg_engagement_rate": 5.5,
                    "trend_percent": -10.0,
                },
                {
                    "advertiser_id": adv_3,
                    "metric_date": baseline_date.isoformat(),
                    "estimated_spend": 1600000.0,
                    "total_ads": 3300,
                    "active_creatives": 240,
                    "channels_used": 920,
                    "avg_engagement_rate": 3.2,
                    "trend_percent": -4.0,
                },
            ]
        )

    storage = {
        "advertisers": [
            {
                "id": adv_1,
                "name": "Binance",
                "slug": "binance",
                "industry_id": crypto_id,
                "logo_url": "https://cdn.example.com/adv/binance.png",
                "website_url": "https://www.binance.com",
                "description": "Global crypto exchange and ecosystem products.",
                "active_creatives_count": 156,
                "estimated_spend_current": 2500000.0,
                "avg_engagement_rate_current": 4.2,
                "total_ads_current": 4500,
                "channels_used_current": 1200,
                "trend_30d": 15.3,
            },
            {
                "id": adv_2,
                "name": "Telegram Premium",
                "slug": "telegram-premium",
                "industry_id": tech_id,
                "logo_url": "https://cdn.example.com/adv/premium.png",
                "website_url": "https://telegram.org",
                "description": "Premium subscription and Telegram features.",
                "active_creatives_count": 89,
                "estimated_spend_current": 1800000.0,
                "avg_engagement_rate_current": 5.8,
                "total_ads_current": 3900,
                "channels_used_current": 2100,
                "trend_30d": 22.1,
            },
            {
                "id": adv_3,
                "name": "1xBet",
                "slug": "1xbet",
                "industry_id": gaming_id,
                "logo_url": "https://cdn.example.com/adv/1xbet.png",
                "website_url": "https://1xbet.example",
                "description": "Gaming and betting promotions.",
                "active_creatives_count": 234,
                "estimated_spend_current": 1500000.0,
                "avg_engagement_rate_current": 3.1,
                "total_ads_current": 3200,
                "channels_used_current": 890,
                "trend_30d": -5.2,
            },
            {
                "id": adv_4,
                "name": "Bybit",
                "slug": "bybit",
                "industry_id": crypto_id,
                "logo_url": "https://cdn.example.com/adv/bybit.png",
                "website_url": "https://www.bybit.com",
                "description": "Crypto trading platform and campaigns.",
                "active_creatives_count": 112,
                "estimated_spend_current": 1200000.0,
                "avg_engagement_rate_current": 3.9,
                "total_ads_current": 3000,
                "channels_used_current": 756,
                "trend_30d": 8.7,
            },
        ],
        "industries": [
            {"id": crypto_id, "slug": "crypto", "name": "Crypto"},
            {"id": tech_id, "slug": "tech", "name": "Tech"},
            {"id": gaming_id, "slug": "gaming", "name": "Gaming"},
        ],
        "advertiser_metrics_daily": metrics,
        "ad_creatives": [
            {
                "advertiser_id": adv_1,
                "posted_at": (today - timedelta(days=5)).isoformat() + "T10:00:00Z",
                "last_seen_at": (today - timedelta(days=1)).isoformat() + "T08:00:00Z",
            },
            {
                "advertiser_id": adv_2,
                "posted_at": (today - timedelta(days=20)).isoformat() + "T10:00:00Z",
                "last_seen_at": (today - timedelta(days=15)).isoformat() + "T08:00:00Z",
            },
            {
                "advertiser_id": adv_3,
                "posted_at": (today - timedelta(days=60)).isoformat() + "T10:00:00Z",
                "last_seen_at": (today - timedelta(days=45)).isoformat() + "T08:00:00Z",
            },
        ],
        "advertiser_top_channels_daily": [
            {
                "advertiser_id": adv_1,
                "snapshot_date": snapshot_date.isoformat(),
                "channel_id": "ch-1",
                "rank": 1,
                "impressions": 8700000,
                "estimated_spend": 520000.0,
                "engagement_rate": 4.6,
            },
            {
                "advertiser_id": adv_1,
                "snapshot_date": snapshot_date.isoformat(),
                "channel_id": "ch-2",
                "rank": 2,
                "impressions": 6500000,
                "estimated_spend": 410000.0,
                "engagement_rate": 4.1,
            },
            {
                "advertiser_id": adv_1,
                "snapshot_date": (today - timedelta(days=1)).isoformat(),
                "channel_id": "ch-3",
                "rank": 1,
                "impressions": 1200000,
                "estimated_spend": 100000.0,
                "engagement_rate": 2.1,
            },
        ],
        "channels": [
            {"id": "ch-1", "name": "Crypto News", "username": "cryptonews"},
            {"id": "ch-2", "name": "Trading Signals", "username": "tradingsignals"},
            {"id": "ch-3", "name": "Old Channel", "username": "oldchannel"},
        ],
    }
    return storage


def _get_fake_supabase(*, include_baseline: bool = True):
    return FakeSupabaseClient(_build_storage(include_baseline=include_baseline))


def test_list_advertisers_base_response_shape():
    supabase_client = _get_fake_supabase()
    app.dependency_overrides[get_supabase] = lambda: supabase_client
    app.dependency_overrides[deps.get_current_user] = _override_current_user

    try:
        with TestClient(app) as client:
            response = client.get("/v1.0/advertisers?time_period_days=30&limit=2")

        assert response.status_code == 200
        body = response.json()
        assert len(body["data"]) == 2
        assert body["data"][0]["rank"] == 1
        assert body["data"][0]["name"] == "Binance"
        assert body["data"][0]["industry_slug"] == "crypto"
        assert body["data"][0]["last_active_at"] is not None
        assert body["meta"]["total_estimate"] == 4
        assert body["meta"]["time_period_days"] == 30
        assert body["meta"]["snapshot_date"] == date.today().isoformat()
        assert body["meta"]["baseline_date"] == (date.today() - timedelta(days=30)).isoformat()
    finally:
        app.dependency_overrides = {}


def test_list_advertisers_search_filters_and_activity_status():
    supabase_client = _get_fake_supabase()
    app.dependency_overrides[get_supabase] = lambda: supabase_client
    app.dependency_overrides[deps.get_current_user] = _override_current_user

    try:
        with TestClient(app) as client:
            response = client.get(
                "/v1.0/advertisers?q=binance&industry_slug=crypto&time_period_days=30&min_spend=500000&min_channels=100&min_engagement=3&activity_status=active&sort_by=trend&sort_order=desc&limit=10"
            )

        assert response.status_code == 200
        body = response.json()
        assert len(body["data"]) == 1
        assert body["data"][0]["slug"] == "binance"
        assert body["data"][0]["rank"] == 1
        assert body["data"][0]["trend"] > 0
    finally:
        app.dependency_overrides = {}


def test_list_advertisers_cursor_pagination_and_rank_continuation():
    supabase_client = _get_fake_supabase()
    app.dependency_overrides[get_supabase] = lambda: supabase_client
    app.dependency_overrides[deps.get_current_user] = _override_current_user

    try:
        with TestClient(app) as client:
            first_page = client.get("/v1.0/advertisers?limit=2")
            assert first_page.status_code == 200
            first_body = first_page.json()
            cursor = first_body["page"]["next_cursor"]
            assert cursor

            second_page = client.get(f"/v1.0/advertisers?limit=2&cursor={cursor}")
            assert second_page.status_code == 200
            second_body = second_page.json()

        assert [item["rank"] for item in first_body["data"]] == [1, 2]
        assert [item["rank"] for item in second_body["data"]] == [3, 4]
    finally:
        app.dependency_overrides = {}


def test_list_advertisers_invalid_cursor():
    supabase_client = _get_fake_supabase()
    app.dependency_overrides[get_supabase] = lambda: supabase_client
    app.dependency_overrides[deps.get_current_user] = _override_current_user

    try:
        with TestClient(app) as client:
            response = client.get("/v1.0/advertisers?cursor=not-a-valid-cursor")

        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid pagination cursor"
    finally:
        app.dependency_overrides = {}


def test_list_advertisers_recent_activity_status():
    supabase_client = _get_fake_supabase()
    app.dependency_overrides[get_supabase] = lambda: supabase_client
    app.dependency_overrides[deps.get_current_user] = _override_current_user

    try:
        with TestClient(app) as client:
            response = client.get("/v1.0/advertisers?activity_status=recent")
        assert response.status_code == 200
        body = response.json()
        slugs = {item["slug"] for item in body["data"]}
        assert "binance" in slugs
        assert "telegram-premium" in slugs
        assert "1xbet" not in slugs
    finally:
        app.dependency_overrides = {}


def test_get_advertisers_summary_with_baseline():
    supabase_client = _get_fake_supabase(include_baseline=True)
    app.dependency_overrides[get_supabase] = lambda: supabase_client
    app.dependency_overrides[deps.get_current_user] = _override_current_user

    try:
        with TestClient(app) as client:
            response = client.get("/v1.0/advertisers/summary?time_period_days=30")

        assert response.status_code == 200
        body = response.json()
        assert body["data"]["active_advertisers"] == 4
        assert body["data"]["total_ad_spend"] > 0
        assert body["data"]["ad_campaigns"] > 0
        assert body["data"]["active_advertisers_delta"] is not None
        assert body["data"]["total_ad_spend_delta"] is not None
        assert body["data"]["ad_campaigns_delta_percent"] is not None
        assert body["meta"]["snapshot_date"] == date.today().isoformat()
    finally:
        app.dependency_overrides = {}


def test_get_advertisers_summary_missing_baseline_sets_deltas_null():
    supabase_client = _get_fake_supabase(include_baseline=False)
    app.dependency_overrides[get_supabase] = lambda: supabase_client
    app.dependency_overrides[deps.get_current_user] = _override_current_user

    try:
        with TestClient(app) as client:
            response = client.get("/v1.0/advertisers/summary?time_period_days=30")

        assert response.status_code == 200
        body = response.json()
        assert body["data"]["active_advertisers_delta"] is None
        assert body["data"]["total_ad_spend_delta"] is None
        assert body["data"]["ad_campaigns_delta"] is None
        assert body["data"]["avg_engagement_rate_delta"] is None
    finally:
        app.dependency_overrides = {}


def test_get_advertiser_detail_success_shape():
    supabase_client = _get_fake_supabase()
    app.dependency_overrides[get_supabase] = lambda: supabase_client
    app.dependency_overrides[deps.get_current_user] = _override_current_user

    try:
        advertiser_id = "2e63db9e-13f7-4204-b8b6-a394f40ca83a"
        with TestClient(app) as client:
            response = client.get(f"/v1.0/advertisers/{advertiser_id}")

        assert response.status_code == 200
        body = response.json()
        assert body["data"]["advertiser_id"] == advertiser_id
        assert body["data"]["name"] == "Binance"
        assert body["data"]["website_url"] == "https://www.binance.com"
        assert len(body["data"]["top_channels"]) == 2
        assert body["data"]["top_channels"][0]["username"].startswith("@")
        assert body["meta"]["snapshot_date"] == date.today().isoformat()
    finally:
        app.dependency_overrides = {}


def test_get_advertiser_detail_not_found():
    supabase_client = _get_fake_supabase()
    app.dependency_overrides[get_supabase] = lambda: supabase_client
    app.dependency_overrides[deps.get_current_user] = _override_current_user

    try:
        with TestClient(app) as client:
            response = client.get("/v1.0/advertisers/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
    finally:
        app.dependency_overrides = {}


def test_advertisers_endpoints_require_auth():
    app.dependency_overrides = {}
    try:
        with TestClient(app) as client:
            list_response = client.get("/v1.0/advertisers")
            summary_response = client.get("/v1.0/advertisers/summary")
            detail_response = client.get("/v1.0/advertisers/2e63db9e-13f7-4204-b8b6-a394f40ca83a")

        assert list_response.status_code == 401
        assert summary_response.status_code == 401
        assert detail_response.status_code == 401
    finally:
        app.dependency_overrides = {}
