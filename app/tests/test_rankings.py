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


def _get_fake_supabase():
    storage = {
        "countries": [
            {"code": "US", "name": "United States"},
            {"code": "DE", "name": "Germany"},
        ],
        "categories": [
            {"id": "cat-tech", "slug": "technology", "name": "Technology"},
            {"id": "cat-news", "slug": "news", "name": "News"},
        ],
        "channels": [
            {"id": "ch-1", "name": "Tech News Daily", "username": "technewsdaily"},
            {"id": "ch-2", "name": "Crypto Insights", "username": "cryptoinsights"},
            {"id": "ch-3", "name": "News Breaking", "username": "newsbreaking"},
            {"id": "ch-4", "name": "AI Weekly", "username": "aiweekly"},
        ],
        "channel_rankings_daily": [
            {
                "snapshot_date": "2026-02-13",
                "ranking_scope": "country",
                "country_code": "US",
                "category_id": None,
                "channel_id": "ch-3",
                "rank": 1,
                "subscribers": 1_450_000,
                "engagement_rate": 6.9,
                "growth_7d": 4.3,
            },
            {
                "snapshot_date": "2026-02-14",
                "ranking_scope": "country",
                "country_code": "US",
                "category_id": None,
                "channel_id": "ch-1",
                "rank": 1,
                "subscribers": 2_100_000,
                "engagement_rate": 4.8,
                "growth_7d": 8.2,
            },
            {
                "snapshot_date": "2026-02-14",
                "ranking_scope": "country",
                "country_code": "US",
                "category_id": None,
                "channel_id": "ch-2",
                "rank": 2,
                "subscribers": 1_800_000,
                "engagement_rate": 6.2,
                "growth_7d": 12.4,
            },
            {
                "snapshot_date": "2026-02-14",
                "ranking_scope": "category",
                "country_code": None,
                "category_id": "cat-tech",
                "channel_id": "ch-1",
                "rank": 1,
                "subscribers": 2_100_000,
                "engagement_rate": 4.8,
                "growth_7d": 8.2,
            },
            {
                "snapshot_date": "2026-02-14",
                "ranking_scope": "category",
                "country_code": None,
                "category_id": "cat-tech",
                "channel_id": "ch-4",
                "rank": 2,
                "subscribers": 1_400_000,
                "engagement_rate": 5.2,
                "growth_7d": 6.1,
            },
        ],
        "ranking_collections": [
            {
                "id": "col-tech",
                "slug": "top-tech",
                "name": "Tech & Startups",
                "description": "Best technology channels",
                "icon": "🚀",
                "is_active": True,
            },
            {
                "id": "col-crypto",
                "slug": "crypto-blockchain",
                "name": "Crypto & Blockchain",
                "description": "Top crypto channels",
                "icon": "💎",
                "is_active": True,
            },
            {
                "id": "col-inactive",
                "slug": "inactive",
                "name": "Inactive Collection",
                "description": "Should not be returned",
                "icon": "🧪",
                "is_active": False,
            },
        ],
        "ranking_collection_channels": [
            {"collection_id": "col-tech", "channel_id": "ch-1"},
            {"collection_id": "col-tech", "channel_id": "ch-3"},
            {"collection_id": "col-crypto", "channel_id": "ch-2"},
        ],
    }
    return FakeSupabaseClient(storage)


def test_list_country_rankings_default_us_latest_snapshot():
    supabase_client = _get_fake_supabase()
    app.dependency_overrides[get_supabase] = lambda: supabase_client
    app.dependency_overrides[deps.get_current_user] = _override_current_user

    try:
        with TestClient(app) as client:
            response = client.get("/v1.0/rankings/countries")

        assert response.status_code == 200
        body = response.json()
        assert body["meta"]["country_code"] == "US"
        assert body["meta"]["country_name"] == "United States"
        assert body["meta"]["snapshot_date"] == "2026-02-14"
        assert body["meta"]["total_ranked_channels"] == 2
        assert [item["rank"] for item in body["data"]] == [1, 2]
    finally:
        app.dependency_overrides = {}


def test_list_country_rankings_with_country_filter_and_limit():
    supabase_client = _get_fake_supabase()
    app.dependency_overrides[get_supabase] = lambda: supabase_client
    app.dependency_overrides[deps.get_current_user] = _override_current_user

    try:
        with TestClient(app) as client:
            response = client.get("/v1.0/rankings/countries?country_code=us&limit=1")

        assert response.status_code == 200
        body = response.json()
        assert body["meta"]["country_code"] == "US"
        assert body["meta"]["applied_limit"] == 1
        assert len(body["data"]) == 1
        assert body["data"][0]["trend_label"] == "growth_7d"
        assert body["data"][0]["context_type"] == "country"
    finally:
        app.dependency_overrides = {}


def test_list_category_rankings_default_technology():
    supabase_client = _get_fake_supabase()
    app.dependency_overrides[get_supabase] = lambda: supabase_client
    app.dependency_overrides[deps.get_current_user] = _override_current_user

    try:
        with TestClient(app) as client:
            response = client.get("/v1.0/rankings/categories")

        assert response.status_code == 200
        body = response.json()
        assert body["meta"]["category_slug"] == "technology"
        assert body["meta"]["category_name"] == "Technology"
        assert body["meta"]["snapshot_date"] == "2026-02-14"
        assert body["meta"]["total_ranked_channels"] == 2
        assert body["data"][0]["context_label"] == "Technology"
        assert body["data"][0]["trend_label"] == "engagement_rate"
        assert body["data"][0]["trend_value"] == body["data"][0]["engagement_rate"]
    finally:
        app.dependency_overrides = {}


def test_list_category_rankings_unknown_slug_returns_empty():
    supabase_client = _get_fake_supabase()
    app.dependency_overrides[get_supabase] = lambda: supabase_client
    app.dependency_overrides[deps.get_current_user] = _override_current_user

    try:
        with TestClient(app) as client:
            response = client.get("/v1.0/rankings/categories?category_slug=missing")

        assert response.status_code == 200
        body = response.json()
        assert body["data"] == []
        assert body["meta"]["category_slug"] == "missing"
        assert body["meta"]["snapshot_date"] is None
        assert body["meta"]["total_ranked_channels"] == 0
    finally:
        app.dependency_overrides = {}


def test_list_collections_cards_only_active_with_counts():
    supabase_client = _get_fake_supabase()
    app.dependency_overrides[get_supabase] = lambda: supabase_client
    app.dependency_overrides[deps.get_current_user] = _override_current_user

    try:
        with TestClient(app) as client:
            response = client.get("/v1.0/rankings/collections?limit=20")

        assert response.status_code == 200
        body = response.json()
        assert body["meta"]["total_active_collections"] == 2
        assert len(body["data"]) == 2
        assert body["data"][0]["name"] == "Crypto & Blockchain"
        assert body["data"][0]["channels_count"] == 1
        assert body["data"][0]["cta_label"] == "Explore"
        assert body["data"][0]["cta_target"] == "/rankings/collections/col-crypto/channels"
        assert body["data"][1]["channels_count"] == 2
    finally:
        app.dependency_overrides = {}


def test_rankings_requires_auth():
    supabase_client = _get_fake_supabase()
    app.dependency_overrides[get_supabase] = lambda: supabase_client

    try:
        with TestClient(app) as client:
            response = client.get("/v1.0/rankings/countries")

        assert response.status_code == 401
    finally:
        app.dependency_overrides = {}


def test_invalid_country_code_validation():
    supabase_client = _get_fake_supabase()
    app.dependency_overrides[get_supabase] = lambda: supabase_client
    app.dependency_overrides[deps.get_current_user] = _override_current_user

    try:
        with TestClient(app) as client:
            response = client.get("/v1.0/rankings/countries?country_code=USA")

        assert response.status_code == 422
    finally:
        app.dependency_overrides = {}
