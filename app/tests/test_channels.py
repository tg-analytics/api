import re

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
        self.or_filters: list = []
        self.orders: list[tuple[str, bool]] = []
        self.limit_value: int | None = None
        self.range_start: int | None = None
        self.range_end: int | None = None
        self.select_count: str | None = None
        self.head = False

    def select(self, *_args, **kwargs):
        self.select_count = kwargs.get("count")
        self.head = bool(kwargs.get("head", False))
        return self

    def eq(self, field, value):
        self.filters.append(lambda row: row.get(field) == value)
        return self

    def gte(self, field, value):
        self.filters.append(
            lambda row: row.get(field) is not None and row.get(field) >= value
        )
        return self

    def lte(self, field, value):
        self.filters.append(
            lambda row: row.get(field) is not None and row.get(field) <= value
        )
        return self

    def or_(self, condition: str):
        match = re.search(r"\*([^*]+)\*", condition)
        if not match:
            return self

        term = match.group(1).lower()
        self.or_filters.append(
            lambda row: term in str(row.get("name", "")).lower()
            or term in str(row.get("username", "")).lower()
        )
        return self

    def order(self, field: str, desc: bool = False, **_kwargs):
        self.orders.append((field, desc))
        return self

    def limit(self, count: int):
        self.limit_value = count
        return self

    def range(self, start: int, end: int):
        self.range_start = start
        self.range_end = end
        return self

    def _apply_order(self, rows: list[dict], field: str, desc: bool) -> list[dict]:
        non_null_rows = [row for row in rows if row.get(field) is not None]
        null_rows = [row for row in rows if row.get(field) is None]
        non_null_rows.sort(key=lambda row: row.get(field), reverse=desc)
        return non_null_rows + null_rows

    def execute(self):
        rows = [
            row.copy()
            for row in self.storage.get(self.table_name, [])
            if all(f(row) for f in self.filters)
            and (not self.or_filters or any(f(row) for f in self.or_filters))
        ]
        total_count = len(rows)

        for field, desc in reversed(self.orders):
            rows = self._apply_order(rows, field, desc)

        if self.range_start is not None and self.range_end is not None:
            rows = rows[self.range_start : self.range_end + 1]
        elif self.limit_value is not None:
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


def _get_fake_supabase():
    channel_id = "9f28253d-8ffd-4d2f-a67c-ebaf0f6ba2f2"
    similar_channel_1 = "f8e98743-1448-4d13-8f8f-b8fbbf272141"
    similar_channel_2 = "4d3ced17-4a8c-4e61-a71f-89dc852f216a"
    tag_id_1 = "11111111-1111-1111-1111-111111111111"
    tag_id_2 = "22222222-2222-2222-2222-222222222222"

    storage = {
        "vw_catalog_channels": [
            {
                "channel_id": channel_id,
                "name": "Tech News Daily",
                "username": "technewsdaily",
                "subscribers": 1_300_000,
                "growth_24h": 2.3,
                "growth_7d": 8.5,
                "growth_30d": 24.2,
                "engagement_rate": 4.8,
                "category_slug": "technology",
                "category_name": "Technology",
                "country_code": "US",
                "status": "verified",
                "verified": True,
                "scam": False,
                "size_bucket": "huge",
                "updated_at": "2026-02-14T10:00:00Z",
            },
            {
                "channel_id": "f8e98743-1448-4d13-8f8f-b8fbbf272141",
                "name": "Crypto Growth Radar",
                "username": "cryptoradar",
                "subscribers": 640_000,
                "growth_24h": 1.9,
                "growth_7d": 9.1,
                "growth_30d": 21.4,
                "engagement_rate": 6.5,
                "category_slug": "cryptocurrencies",
                "category_name": "Cryptocurrencies",
                "country_code": "US",
                "status": "verified",
                "verified": True,
                "scam": False,
                "size_bucket": "large",
                "updated_at": "2026-02-14T09:00:00Z",
            },
            {
                "channel_id": "4d3ced17-4a8c-4e61-a71f-89dc852f216a",
                "name": "Crypto Alpha",
                "username": "cryptoalpha",
                "subscribers": 520_000,
                "growth_24h": 1.2,
                "growth_7d": 6.8,
                "growth_30d": 14.9,
                "engagement_rate": 5.3,
                "category_slug": "cryptocurrencies",
                "category_name": "Cryptocurrencies",
                "country_code": "US",
                "status": "verified",
                "verified": True,
                "scam": False,
                "size_bucket": "large",
                "updated_at": "2026-02-14T08:00:00Z",
            },
            {
                "channel_id": "7f2cfed7-8dfd-4bc4-8d43-c09d6d6f4f9b",
                "name": "Crypto Risky Bets",
                "username": "cryptoriskybets",
                "subscribers": 410_000,
                "growth_24h": 0.8,
                "growth_7d": 11.0,
                "growth_30d": 32.8,
                "engagement_rate": 2.1,
                "category_slug": "cryptocurrencies",
                "category_name": "Cryptocurrencies",
                "country_code": "US",
                "status": "scam",
                "verified": False,
                "scam": True,
                "size_bucket": "large",
                "updated_at": "2026-02-14T07:00:00Z",
            },
        ],
        "vw_channel_overview": [
            {
                "channel_id": channel_id,
                "telegram_channel_id": 100001,
                "name": "Tech News Daily",
                "username": "technewsdaily",
                "avatar_url": "https://cdn.example.com/ch/tn.png",
                "description": "Your daily source for the latest technology news.",
                "status": "verified",
                "country_code": "US",
                "category_slug": "technology",
                "category_name": "Technology",
                "about_text": "Trusted by 1M+ readers.",
                "website_url": "https://technewsdaily.example",
                "subscribers": 1_300_000,
                "avg_views": 480_000,
                "engagement_rate": 3.2,
                "posts_per_day": 4.2,
                "incoming_30d": 12_500,
                "outgoing_30d": 3_200,
            }
        ],
        "channel_metrics_daily": [
            {
                "channel_id": channel_id,
                "metric_date": "2026-02-14",
                "subscribers": 1_300_000,
                "avg_views": 480_000,
                "engagement_rate": 3.2,
                "posts_per_day": 4.2,
            },
            {
                "channel_id": channel_id,
                "metric_date": "2026-02-13",
                "subscribers": 1_250_000,
                "avg_views": 470_000,
                "engagement_rate": 3.0,
                "posts_per_day": 4.4,
            },
            {
                "channel_id": channel_id,
                "metric_date": "2026-01-16",
                "subscribers": 1_200_000,
                "avg_views": 450_000,
                "engagement_rate": 2.9,
                "posts_per_day": 4.7,
            },
        ],
        "channel_similarities": [
            {
                "channel_id": channel_id,
                "similar_channel_id": similar_channel_1,
                "similarity_score": 0.82,
            },
            {
                "channel_id": channel_id,
                "similar_channel_id": similar_channel_2,
                "similarity_score": 0.61,
            },
        ],
        "channels": [
            {
                "id": similar_channel_1,
                "name": "Crypto Growth Radar",
                "username": "cryptoradar",
                "subscribers_current": 640_000,
            },
            {
                "id": similar_channel_2,
                "name": "Crypto Alpha",
                "username": "cryptoalpha",
                "subscribers_current": 520_000,
            },
        ],
        "channel_tags": [
            {"channel_id": channel_id, "tag_id": tag_id_1, "relevance_score": 92.5},
            {"channel_id": channel_id, "tag_id": tag_id_2, "relevance_score": 77.0},
        ],
        "tags": [
            {"id": tag_id_1, "slug": "technology", "name": "Technology", "usage_count": 2},
            {"id": tag_id_2, "slug": "news", "name": "News", "usage_count": 999},
        ],
        "posts": [
            {
                "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                "channel_id": channel_id,
                "telegram_message_id": 9001,
                "published_at": "2026-02-14T10:00:00Z",
                "title": "Breaking: New AI model released",
                "content_text": "New AI model released with unprecedented capabilities.",
                "views_count": 125000,
                "reactions_count": 4200,
                "comments_count": 640,
                "forwards_count": 1800,
                "external_post_url": "https://t.me/technewsdaily/9001",
                "is_deleted": False,
            },
            {
                "id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                "channel_id": channel_id,
                "telegram_message_id": 9002,
                "published_at": "2026-02-14T08:00:00Z",
                "title": "Tip of the day",
                "content_text": "How to optimize your workflow with five simple tools.",
                "views_count": 89000,
                "reactions_count": 2100,
                "comments_count": 220,
                "forwards_count": 920,
                "external_post_url": "https://t.me/technewsdaily/9002",
                "is_deleted": False,
            },
            {
                "id": "cccccccc-cccc-cccc-cccc-cccccccccccc",
                "channel_id": channel_id,
                "telegram_message_id": 9003,
                "published_at": "2026-02-13T20:00:00Z",
                "title": "Deleted post",
                "content_text": "Should not be returned.",
                "views_count": 67000,
                "reactions_count": 1500,
                "comments_count": 180,
                "forwards_count": 450,
                "external_post_url": "https://t.me/technewsdaily/9003",
                "is_deleted": True,
            },
        ],
    }
    return FakeSupabaseClient(storage)


def test_list_channels_base_response_shape():
    supabase_client = _get_fake_supabase()
    app.dependency_overrides[get_supabase] = lambda: supabase_client
    app.dependency_overrides[deps.get_current_user] = _override_current_user

    try:
        with TestClient(app) as client:
            response = client.get(
                "/v1.0/channels?limit=2&sort_by=subscribers&sort_order=desc"
            )

        assert response.status_code == 200
        body = response.json()
        assert len(body["data"]) == 2
        assert body["data"][0]["name"] == "Tech News Daily"
        assert body["data"][0]["username"] == "@technewsdaily"
        assert body["page"]["has_more"] is True
        assert body["page"]["next_cursor"] is not None
        assert body["meta"]["total_estimate"] == 4
    finally:
        app.dependency_overrides = {}


def test_list_channels_search_and_filters():
    supabase_client = _get_fake_supabase()
    app.dependency_overrides[get_supabase] = lambda: supabase_client
    app.dependency_overrides[deps.get_current_user] = _override_current_user

    try:
        with TestClient(app) as client:
            response = client.get(
                "/v1.0/channels"
                "?q=crypto"
                "&country_code=US"
                "&category_slug=cryptocurrencies"
                "&size_bucket=large"
                "&er_min=3"
                "&er_max=10"
                "&verified=true"
                "&sort_by=growth_7d"
                "&sort_order=desc"
                "&limit=10"
            )

        assert response.status_code == 200
        body = response.json()
        assert len(body["data"]) == 2
        assert body["data"][0]["name"] == "Crypto Growth Radar"
        assert body["data"][1]["name"] == "Crypto Alpha"
        assert body["data"][0]["verified"] is True
        assert body["data"][0]["country_code"] == "US"
        assert body["meta"]["total_estimate"] == 2
    finally:
        app.dependency_overrides = {}


def test_list_channels_cursor_pagination():
    supabase_client = _get_fake_supabase()
    app.dependency_overrides[get_supabase] = lambda: supabase_client
    app.dependency_overrides[deps.get_current_user] = _override_current_user

    try:
        with TestClient(app) as client:
            first_page = client.get("/v1.0/channels?limit=2&sort_by=subscribers&sort_order=desc")

            assert first_page.status_code == 200
            first_data = first_page.json()
            next_cursor = first_data["page"]["next_cursor"]
            assert next_cursor is not None

            second_page = client.get(
                f"/v1.0/channels?limit=2&sort_by=subscribers&sort_order=desc&cursor={next_cursor}"
            )

        assert second_page.status_code == 200
        second_data = second_page.json()
        assert len(second_data["data"]) == 2
        assert second_data["data"][0]["name"] == "Crypto Alpha"
        assert second_data["page"]["has_more"] is False
        assert second_data["page"]["next_cursor"] is None
    finally:
        app.dependency_overrides = {}


def test_list_channels_requires_auth():
    supabase_client = _get_fake_supabase()
    app.dependency_overrides[get_supabase] = lambda: supabase_client

    try:
        with TestClient(app) as client:
            response = client.get("/v1.0/channels")

        assert response.status_code == 401
    finally:
        app.dependency_overrides = {}


def test_list_channels_invalid_cursor():
    supabase_client = _get_fake_supabase()
    app.dependency_overrides[get_supabase] = lambda: supabase_client
    app.dependency_overrides[deps.get_current_user] = _override_current_user

    try:
        with TestClient(app) as client:
            response = client.get("/v1.0/channels?cursor=not-a-valid-cursor")

        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid pagination cursor"
    finally:
        app.dependency_overrides = {}


def test_get_channel_overview_success_shape():
    supabase_client = _get_fake_supabase()
    app.dependency_overrides[get_supabase] = lambda: supabase_client
    app.dependency_overrides[deps.get_current_user] = _override_current_user

    try:
        with TestClient(app) as client:
            response = client.get("/v1.0/channels/9f28253d-8ffd-4d2f-a67c-ebaf0f6ba2f2/overview")

        assert response.status_code == 200
        body = response.json()
        assert body["data"]["channel"]["name"] == "Tech News Daily"
        assert body["data"]["channel"]["username"] == "@technewsdaily"
        assert body["data"]["kpis"]["subscribers"]["value"] == 1300000
        assert body["data"]["chart"]["range"] == "30d"
        assert len(body["data"]["chart"]["points"]) == 3
        assert len(body["data"]["similar_channels"]) == 2
        assert len(body["data"]["tags"]) == 2
        assert len(body["data"]["recent_posts"]) == 2
        assert body["data"]["inout_30d"]["incoming"] == 12500
        assert body["data"]["incoming_30d"] == 12500
        assert body["meta"] == {}
    finally:
        app.dependency_overrides = {}


def test_get_channel_overview_uses_tag_relevance():
    supabase_client = _get_fake_supabase()
    app.dependency_overrides[get_supabase] = lambda: supabase_client
    app.dependency_overrides[deps.get_current_user] = _override_current_user

    try:
        with TestClient(app) as client:
            response = client.get("/v1.0/channels/9f28253d-8ffd-4d2f-a67c-ebaf0f6ba2f2/overview")

        assert response.status_code == 200
        tags = response.json()["data"]["tags"]
        assert tags[0]["slug"] == "technology"
        assert tags[0]["relevance_score"] == 92.5
        assert tags[1]["slug"] == "news"
        assert tags[1]["relevance_score"] == 77.0
    finally:
        app.dependency_overrides = {}


def test_get_channel_overview_excludes_deleted_posts():
    supabase_client = _get_fake_supabase()
    app.dependency_overrides[get_supabase] = lambda: supabase_client
    app.dependency_overrides[deps.get_current_user] = _override_current_user

    try:
        with TestClient(app) as client:
            response = client.get("/v1.0/channels/9f28253d-8ffd-4d2f-a67c-ebaf0f6ba2f2/overview")

        assert response.status_code == 200
        recent_posts = response.json()["data"]["recent_posts"]
        message_ids = [post["telegram_message_id"] for post in recent_posts]
        assert 9003 not in message_ids
    finally:
        app.dependency_overrides = {}


def test_get_channel_overview_not_found():
    supabase_client = _get_fake_supabase()
    app.dependency_overrides[get_supabase] = lambda: supabase_client
    app.dependency_overrides[deps.get_current_user] = _override_current_user

    try:
        with TestClient(app) as client:
            response = client.get("/v1.0/channels/00000000-0000-0000-0000-000000000000/overview")

        assert response.status_code == 404
        assert response.json()["detail"] == "Channel not found"
    finally:
        app.dependency_overrides = {}


def test_get_channel_overview_requires_auth():
    supabase_client = _get_fake_supabase()
    app.dependency_overrides[get_supabase] = lambda: supabase_client

    try:
        with TestClient(app) as client:
            response = client.get("/v1.0/channels/9f28253d-8ffd-4d2f-a67c-ebaf0f6ba2f2/overview")

        assert response.status_code == 401
    finally:
        app.dependency_overrides = {}


def test_get_channel_overview_kpi_delta_computation():
    supabase_client = _get_fake_supabase()
    app.dependency_overrides[get_supabase] = lambda: supabase_client
    app.dependency_overrides[deps.get_current_user] = _override_current_user

    try:
        with TestClient(app) as client:
            response = client.get("/v1.0/channels/9f28253d-8ffd-4d2f-a67c-ebaf0f6ba2f2/overview")

        assert response.status_code == 200
        kpis = response.json()["data"]["kpis"]
        assert kpis["subscribers"]["delta"] == 100000
        assert kpis["subscribers"]["delta_percent"] == 100000 / 1200000 * 100
        assert kpis["posts_per_day"]["delta"] == -0.5
    finally:
        app.dependency_overrides = {}
