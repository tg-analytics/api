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
    storage = {
        "vw_catalog_channels": [
            {
                "channel_id": "9f28253d-8ffd-4d2f-a67c-ebaf0f6ba2f2",
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
        ]
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
