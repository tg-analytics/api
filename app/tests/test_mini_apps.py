import re
from datetime import date, datetime, timedelta
from typing import Any

from fastapi.testclient import TestClient

from app.api import deps
from app.db.base import get_supabase
from app.main import app


class FakeResponse:
    def __init__(self, data, count: int | None = None):
        self.data = data
        self.count = count


def _coerce_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return value
    return value


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
        def _predicate(row: dict[str, Any]) -> bool:
            row_value = row.get(field)
            if row_value is None:
                return False
            row_comp = _coerce_value(row_value)
            filter_comp = _coerce_value(value)
            try:
                return row_comp >= filter_comp
            except TypeError:
                return False

        self.filters.append(_predicate)
        return self

    def lte(self, field, value):
        def _predicate(row: dict[str, Any]) -> bool:
            row_value = row.get(field)
            if row_value is None:
                return False
            row_comp = _coerce_value(row_value)
            filter_comp = _coerce_value(value)
            try:
                return row_comp <= filter_comp
            except TypeError:
                return False

        self.filters.append(_predicate)
        return self

    def or_(self, condition: str):
        match = re.search(r"\*([^*]+)\*", condition)
        if not match:
            return self

        term = match.group(1).lower()
        self.or_filters.append(
            lambda row: term in str(row.get("name", "")).lower()
            or term in str(row.get("slug", "")).lower()
            or term in str(row.get("description", "")).lower()
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
        non_null_rows.sort(key=lambda row: _coerce_value(row.get(field)), reverse=desc)
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


def _build_storage(*, include_30d_baseline: bool = True) -> dict[str, list[dict]]:
    today = date.today()
    latest = today
    baseline_7 = today - timedelta(days=7)
    baseline_30 = today - timedelta(days=30)

    app_1 = "fbd37667-230f-4c5b-b0f6-243b02608e11"
    app_2 = "f9bc6f4f-b14a-421f-964f-a973236ec820"
    app_3 = "8f33af72-4a15-4b6d-ae56-8ea6a0985262"
    app_4 = "0b4f1ef1-30e3-47f0-89f1-5cf25114ba3b"

    mini_apps = [
        {"id": app_1, "launched_at": (today - timedelta(days=240)).isoformat()},
        {"id": app_2, "launched_at": (today - timedelta(days=320)).isoformat()},
        {"id": app_3, "launched_at": (today - timedelta(days=120)).isoformat()},
        {"id": app_4, "launched_at": (today - timedelta(days=450)).isoformat()},
    ]

    metrics_rows = [
        {
            "mini_app_id": app_1,
            "metric_date": latest.isoformat(),
            "daily_users": 2_500_000,
            "sessions": 98_000_000,
            "avg_session_seconds": 272,
        },
        {
            "mini_app_id": app_2,
            "metric_date": latest.isoformat(),
            "daily_users": 1_800_000,
            "sessions": 76_000_000,
            "avg_session_seconds": 268,
        },
        {
            "mini_app_id": app_3,
            "metric_date": latest.isoformat(),
            "daily_users": 1_200_000,
            "sessions": 54_000_000,
            "avg_session_seconds": 295,
        },
        {
            "mini_app_id": app_4,
            "metric_date": latest.isoformat(),
            "daily_users": 450_000,
            "sessions": 16_000_000,
            "avg_session_seconds": 260,
        },
        {
            "mini_app_id": app_1,
            "metric_date": baseline_7.isoformat(),
            "daily_users": 2_300_000,
            "sessions": 90_000_000,
            "avg_session_seconds": 260,
        },
        {
            "mini_app_id": app_2,
            "metric_date": baseline_7.isoformat(),
            "daily_users": 1_700_000,
            "sessions": 70_000_000,
            "avg_session_seconds": 262,
        },
        {
            "mini_app_id": app_3,
            "metric_date": baseline_7.isoformat(),
            "daily_users": 1_050_000,
            "sessions": 49_000_000,
            "avg_session_seconds": 280,
        },
        {
            "mini_app_id": app_4,
            "metric_date": baseline_7.isoformat(),
            "daily_users": 420_000,
            "sessions": 15_000_000,
            "avg_session_seconds": 250,
        },
    ]

    if include_30d_baseline:
        metrics_rows.extend(
            [
                {
                    "mini_app_id": app_1,
                    "metric_date": baseline_30.isoformat(),
                    "daily_users": 2_100_000,
                    "sessions": 85_000_000,
                    "avg_session_seconds": 258,
                },
                {
                    "mini_app_id": app_2,
                    "metric_date": baseline_30.isoformat(),
                    "daily_users": 1_600_000,
                    "sessions": 66_000_000,
                    "avg_session_seconds": 259,
                },
                {
                    "mini_app_id": app_3,
                    "metric_date": baseline_30.isoformat(),
                    "daily_users": 980_000,
                    "sessions": 45_000_000,
                    "avg_session_seconds": 275,
                },
                {
                    "mini_app_id": app_4,
                    "metric_date": baseline_30.isoformat(),
                    "daily_users": 380_000,
                    "sessions": 13_000_000,
                    "avg_session_seconds": 248,
                },
            ]
        )

    return {
        "mini_apps": mini_apps,
        "vw_mini_apps_latest": [
            {
                "mini_app_id": app_1,
                "name": "Hamster Kombat",
                "slug": "hamster-kombat",
                "description": "Tap-to-earn crypto game with hamster theme.",
                "category_slug": "games",
                "daily_users": 2_500_000,
                "total_users": 45_000_000,
                "sessions": 98_000_000,
                "rating": 4.8,
                "growth_weekly": 15.2,
                "launched_at": (today - timedelta(days=240)).isoformat(),
            },
            {
                "mini_app_id": app_2,
                "name": "Notcoin",
                "slug": "notcoin",
                "description": "Popular tap-to-earn mining game.",
                "category_slug": "games",
                "daily_users": 1_800_000,
                "total_users": 35_000_000,
                "sessions": 76_000_000,
                "rating": 4.6,
                "growth_weekly": 8.5,
                "launched_at": (today - timedelta(days=320)).isoformat(),
            },
            {
                "mini_app_id": app_3,
                "name": "Wallet",
                "slug": "wallet",
                "description": "Official Telegram crypto wallet.",
                "category_slug": "finance",
                "daily_users": 1_200_000,
                "total_users": 28_000_000,
                "sessions": 54_000_000,
                "rating": 4.9,
                "growth_weekly": 22.3,
                "launched_at": (today - timedelta(days=120)).isoformat(),
            },
            {
                "mini_app_id": app_4,
                "name": "Fragment",
                "slug": "fragment",
                "description": "NFT marketplace for usernames and numbers.",
                "category_slug": "finance",
                "daily_users": 450_000,
                "total_users": 8_500_000,
                "sessions": 16_000_000,
                "rating": 4.7,
                "growth_weekly": 12.1,
                "launched_at": (today - timedelta(days=450)).isoformat(),
            },
        ],
        "mini_app_metrics_daily": metrics_rows,
    }


def _get_fake_supabase(*, include_30d_baseline: bool = True):
    return FakeSupabaseClient(_build_storage(include_30d_baseline=include_30d_baseline))


def test_list_mini_apps_base_response_shape():
    supabase_client = _get_fake_supabase()
    app.dependency_overrides[get_supabase] = lambda: supabase_client
    app.dependency_overrides[deps.get_current_user] = _override_current_user

    try:
        with TestClient(app) as client:
            response = client.get("/v1.0/mini-apps?limit=2&sort_by=daily_users&sort_order=desc")

        assert response.status_code == 200
        body = response.json()
        assert len(body["data"]) == 2
        assert body["data"][0]["name"] == "Hamster Kombat"
        assert body["page"]["has_more"] is True
        assert body["page"]["next_cursor"] is not None
        assert body["meta"]["total_estimate"] == 4
    finally:
        app.dependency_overrides = {}


def test_list_mini_apps_search_and_filters():
    supabase_client = _get_fake_supabase()
    app.dependency_overrides[get_supabase] = lambda: supabase_client
    app.dependency_overrides[deps.get_current_user] = _override_current_user

    try:
        with TestClient(app) as client:
            response = client.get(
                "/v1.0/mini-apps"
                "?q=wallet"
                "&category_slug=finance"
                "&min_daily_users=100000"
                "&min_rating=4.5"
                "&launch_within_days=180"
                "&min_growth=10"
                "&sort_by=growth"
                "&sort_order=desc"
                "&limit=10"
            )

        assert response.status_code == 200
        body = response.json()
        assert len(body["data"]) == 1
        assert body["data"][0]["name"] == "Wallet"
        assert body["data"][0]["category_slug"] == "finance"
        assert body["meta"]["total_estimate"] == 1
    finally:
        app.dependency_overrides = {}


def test_list_mini_apps_sort_by_growth_desc():
    supabase_client = _get_fake_supabase()
    app.dependency_overrides[get_supabase] = lambda: supabase_client
    app.dependency_overrides[deps.get_current_user] = _override_current_user

    try:
        with TestClient(app) as client:
            response = client.get("/v1.0/mini-apps?sort_by=growth&sort_order=desc&limit=10")

        assert response.status_code == 200
        names = [row["name"] for row in response.json()["data"]]
        assert names == ["Wallet", "Hamster Kombat", "Fragment", "Notcoin"]
    finally:
        app.dependency_overrides = {}


def test_list_mini_apps_cursor_pagination():
    supabase_client = _get_fake_supabase()
    app.dependency_overrides[get_supabase] = lambda: supabase_client
    app.dependency_overrides[deps.get_current_user] = _override_current_user

    try:
        with TestClient(app) as client:
            first_page = client.get("/v1.0/mini-apps?limit=2&sort_by=daily_users&sort_order=desc")
            assert first_page.status_code == 200

            next_cursor = first_page.json()["page"]["next_cursor"]
            assert next_cursor is not None

            second_page = client.get(
                f"/v1.0/mini-apps?limit=2&sort_by=daily_users&sort_order=desc&cursor={next_cursor}"
            )

        assert second_page.status_code == 200
        second_data = second_page.json()
        assert len(second_data["data"]) == 2
        assert second_data["data"][0]["name"] == "Wallet"
        assert second_data["page"]["has_more"] is False
        assert second_data["page"]["next_cursor"] is None
    finally:
        app.dependency_overrides = {}


def test_list_mini_apps_invalid_cursor():
    supabase_client = _get_fake_supabase()
    app.dependency_overrides[get_supabase] = lambda: supabase_client
    app.dependency_overrides[deps.get_current_user] = _override_current_user

    try:
        with TestClient(app) as client:
            response = client.get("/v1.0/mini-apps?cursor=not-a-valid-cursor")

        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid pagination cursor"
    finally:
        app.dependency_overrides = {}


def test_list_mini_apps_requires_auth():
    supabase_client = _get_fake_supabase()
    app.dependency_overrides[get_supabase] = lambda: supabase_client

    try:
        with TestClient(app) as client:
            response = client.get("/v1.0/mini-apps")

        assert response.status_code == 401
    finally:
        app.dependency_overrides = {}


def test_get_mini_apps_summary_7d():
    supabase_client = _get_fake_supabase()
    app.dependency_overrides[get_supabase] = lambda: supabase_client
    app.dependency_overrides[deps.get_current_user] = _override_current_user

    try:
        with TestClient(app) as client:
            response = client.get("/v1.0/mini-apps/summary?period=7d")

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["total_mini_apps"] == 4
        assert data["daily_active_users"] == 5_950_000
        assert data["total_sessions"] == 244_000_000
        assert data["avg_session_seconds"] == 274
        assert data["total_mini_apps_delta"] == 0
        assert data["daily_active_users_delta"] == 480_000
        assert data["total_sessions_delta"] == 20_000_000
        assert data["avg_session_seconds_delta"] == 11
    finally:
        app.dependency_overrides = {}


def test_get_mini_apps_summary_30d():
    supabase_client = _get_fake_supabase()
    app.dependency_overrides[get_supabase] = lambda: supabase_client
    app.dependency_overrides[deps.get_current_user] = _override_current_user

    try:
        with TestClient(app) as client:
            response = client.get("/v1.0/mini-apps/summary?period=30d")

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["daily_active_users_delta"] == 890_000
        assert data["total_sessions_delta"] == 35_000_000
        assert data["avg_session_seconds_delta"] == 14
    finally:
        app.dependency_overrides = {}


def test_get_mini_apps_summary_missing_baseline():
    supabase_client = _get_fake_supabase(include_30d_baseline=False)
    app.dependency_overrides[get_supabase] = lambda: supabase_client
    app.dependency_overrides[deps.get_current_user] = _override_current_user

    try:
        with TestClient(app) as client:
            response = client.get("/v1.0/mini-apps/summary?period=30d")

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["daily_active_users"] == 5_950_000
        assert data["daily_active_users_delta"] is None
        assert data["daily_active_users_delta_percent"] is None
        assert data["total_sessions_delta"] is None
        assert data["total_sessions_delta_percent"] is None
        assert data["avg_session_seconds_delta"] is None
    finally:
        app.dependency_overrides = {}


def test_get_mini_apps_summary_requires_auth():
    supabase_client = _get_fake_supabase()
    app.dependency_overrides[get_supabase] = lambda: supabase_client

    try:
        with TestClient(app) as client:
            response = client.get("/v1.0/mini-apps/summary?period=7d")

        assert response.status_code == 401
    finally:
        app.dependency_overrides = {}
