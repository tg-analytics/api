from fastapi.testclient import TestClient

from app.api import deps
from app.db.base import get_supabase
from app.main import app


class FakeResponse:
    def __init__(self, data):
        self.data = data


class FakeTableQuery:
    def __init__(self, table_name: str, storage: dict[str, list[dict]]):
        self.table_name = table_name
        self.storage = storage
        self.filters: list = []
        self.action = "select"
        self.payload = None
        self.limit_value: int | None = None

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, field, value):
        self.filters.append(lambda row: row.get(field) == value)
        return self

    def is_(self, field, value):
        if value == "null":
            self.filters.append(lambda row: row.get(field) is None)
        else:
            self.filters.append(lambda row: row.get(field) == value)
        return self

    def limit(self, value: int):
        self.limit_value = value
        return self

    def insert(self, payload: dict):
        self.action = "insert"
        self.payload = payload
        return self

    def update(self, payload: dict):
        self.action = "update"
        self.payload = payload
        return self

    def execute(self):
        rows = [
            row for row in self.storage.get(self.table_name, []) if all(f(row) for f in self.filters)
        ]

        if self.action == "select":
            if self.limit_value is not None:
                rows = rows[: self.limit_value]
            return FakeResponse([row.copy() for row in rows])

        if self.action == "insert":
            new_row = self.payload.copy()
            self.storage.setdefault(self.table_name, []).append(new_row)
            return FakeResponse([new_row.copy()])

        if self.action == "update":
            updated = []
            for row in self.storage.get(self.table_name, []):
                if all(f(row) for f in self.filters):
                    row.update(self.payload)
                    updated.append(row.copy())
            return FakeResponse(updated)

        return FakeResponse([])


class FakeSupabaseClient:
    def __init__(self, storage: dict[str, list[dict]]):
        self.storage = storage

    def table(self, table_name: str):
        return FakeTableQuery(table_name, self.storage)


def _override_current_user():
    return {"id": "user-1", "email": "user@example.com"}


def _setup(storage: dict[str, list[dict]]):
    app.dependency_overrides[get_supabase] = lambda: FakeSupabaseClient(storage)
    app.dependency_overrides[deps.get_current_user] = _override_current_user


def test_get_preferences_creates_defaults_when_missing():
    storage = {
        "users": [{"id": "user-1", "email": "user@example.com"}],
        "user_preferences": [],
    }
    _setup(storage)

    try:
        with TestClient(app) as client:
            response = client.get("/v1.0/users/me/preferences")

        assert response.status_code == 200
        body = response.json()
        assert body["data"]["language_code"] == "en"
        assert body["data"]["timezone"] == "UTC"
        assert body["data"]["theme"] == "system"
        assert len(storage["user_preferences"]) == 1
    finally:
        app.dependency_overrides = {}


def test_patch_preferences_partial_update():
    storage = {
        "users": [{"id": "user-1", "email": "user@example.com"}],
        "user_preferences": [
            {
                "user_id": "user-1",
                "language_code": "en",
                "timezone": "UTC",
                "theme": "system",
            }
        ],
    }
    _setup(storage)

    try:
        with TestClient(app) as client:
            response = client.patch(
                "/v1.0/users/me/preferences",
                json={"theme": "dark"},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["data"]["theme"] == "dark"
        assert storage["user_preferences"][0]["theme"] == "dark"
    finally:
        app.dependency_overrides = {}


def test_patch_notification_settings_partial_update_and_default_create():
    storage = {
        "users": [{"id": "user-1", "email": "user@example.com"}],
        "user_notification_settings": [],
    }
    _setup(storage)

    try:
        with TestClient(app) as client:
            response = client.patch(
                "/v1.0/users/me/notifications",
                json={"push_notifications": True},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["data"]["push_notifications"] is True
        assert body["data"]["email_notifications"] is True
        assert len(storage["user_notification_settings"]) == 1
    finally:
        app.dependency_overrides = {}


def test_preferences_requires_auth():
    storage = {
        "users": [{"id": "user-1", "email": "user@example.com"}],
        "user_preferences": [],
    }
    app.dependency_overrides[get_supabase] = lambda: FakeSupabaseClient(storage)

    try:
        with TestClient(app) as client:
            response = client.get("/v1.0/users/me/preferences")
        assert response.status_code == 401
    finally:
        app.dependency_overrides = {}
