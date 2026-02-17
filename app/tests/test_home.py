from fastapi.testclient import TestClient

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
        rows = [row.copy() for row in self.storage.get(self.table_name, [])]
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


def _get_fake_supabase():
    storage = {
        "categories": [
            {"slug": "travel", "name": "Travel", "icon": "plane", "channels_count": 24100},
            {"slug": "art-design", "name": "Art & Design", "icon": "palette", "channels_count": 62800},
            {"slug": "books", "name": "Books", "icon": "book-open", "channels_count": 35300},
            {"slug": "beauty", "name": "Beauty", "icon": "sparkles", "channels_count": 65200},
            {"slug": "career", "name": "Career", "icon": None, "channels_count": 18400},
            {"slug": "business", "name": "Business", "icon": "briefcase-business", "channels_count": 80800},
            {
                "slug": "economy-and-finance",
                "name": "Economy & Finance",
                "icon": "landmark",
                "channels_count": 76800,
            },
            {"slug": "cryptocurrency", "name": "Cryptocurrency", "icon": "coins", "channels_count": 9800},
            {"slug": "e-commerce", "name": "E-commerce", "icon": "shopping-bag", "channels_count": 1800},
            {"slug": "education", "name": "Education", "icon": "graduation-cap", "channels_count": 2800},
            {"slug": "facts", "name": "Facts", "icon": "clipboard-list", "channels_count": 8900},
        ]
    }
    return FakeSupabaseClient(storage)


def test_get_home_categories_base_response_shape():
    supabase_client = _get_fake_supabase()
    app.dependency_overrides[get_supabase] = lambda: supabase_client

    try:
        with TestClient(app) as client:
            response = client.get("/v1.0/home/categories?limit=5")

        assert response.status_code == 200
        body = response.json()
        assert [item["name"] for item in body["data"]] == [
            "Art & Design",
            "Beauty",
            "Books",
            "Business",
            "Career",
        ]
        assert body["data"][0]["icon"] == "palette"
        assert body["data"][4]["icon"] is None
        assert body["page"]["has_more"] is True
        assert body["page"]["next_cursor"] == "eyJvZmZzZXQiOjV9"
        assert body["meta"]["total_estimate"] == 11
    finally:
        app.dependency_overrides = {}


def test_get_home_categories_cursor_pagination():
    supabase_client = _get_fake_supabase()
    app.dependency_overrides[get_supabase] = lambda: supabase_client

    try:
        with TestClient(app) as client:
            first_page = client.get("/v1.0/home/categories?limit=5")
            assert first_page.status_code == 200
            next_cursor = first_page.json()["page"]["next_cursor"]

            second_page = client.get(f"/v1.0/home/categories?limit=5&cursor={next_cursor}")

        assert second_page.status_code == 200
        body = second_page.json()
        assert [item["name"] for item in body["data"]] == [
            "Cryptocurrency",
            "E-commerce",
            "Economy & Finance",
            "Education",
            "Facts",
        ]
        assert body["page"]["has_more"] is True
        assert body["page"]["next_cursor"] == "eyJvZmZzZXQiOjEwfQ=="
    finally:
        app.dependency_overrides = {}


def test_get_home_categories_supports_unpadded_cursor_example():
    supabase_client = _get_fake_supabase()
    app.dependency_overrides[get_supabase] = lambda: supabase_client

    try:
        with TestClient(app) as client:
            response = client.get("/v1.0/home/categories?limit=5&cursor=eyJvZmZzZXQiOjV9")

        assert response.status_code == 200
        body = response.json()
        assert body["data"][0]["name"] == "Cryptocurrency"
    finally:
        app.dependency_overrides = {}


def test_get_home_categories_invalid_cursor():
    supabase_client = _get_fake_supabase()
    app.dependency_overrides[get_supabase] = lambda: supabase_client

    try:
        with TestClient(app) as client:
            response = client.get("/v1.0/home/categories?cursor=not-a-valid-cursor")

        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid pagination cursor"
    finally:
        app.dependency_overrides = {}


def test_get_home_categories_is_public_without_auth():
    supabase_client = _get_fake_supabase()
    app.dependency_overrides[get_supabase] = lambda: supabase_client

    try:
        with TestClient(app) as client:
            response = client.get("/v1.0/home/categories")

        assert response.status_code == 200
    finally:
        app.dependency_overrides = {}
