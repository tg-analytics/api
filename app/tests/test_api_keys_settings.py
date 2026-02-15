from __future__ import annotations

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
        self.orders: list[tuple[str, bool]] = []

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

    def in_(self, field, values):
        allowed = set(values)
        self.filters.append(lambda row: row.get(field) in allowed)
        return self

    def gte(self, field, value):
        self.filters.append(lambda row: str(row.get(field)) >= str(value))
        return self

    def lte(self, field, value):
        self.filters.append(lambda row: str(row.get(field)) <= str(value))
        return self

    def limit(self, value: int):
        self._limit = value
        return self

    def order(self, field: str, desc: bool = False, **_kwargs):
        self.orders.append((field, desc))
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
            rows = [row.copy() for row in rows]
            for field, desc in reversed(self.orders):
                rows.sort(key=lambda row: row.get(field), reverse=desc)
            if hasattr(self, "_limit"):
                rows = rows[: self._limit]
            return FakeResponse(rows)

        if self.action == "insert":
            new_row = self.payload.copy()
            if "id" not in new_row:
                new_row["id"] = f"key-{len(self.storage.get(self.table_name, [])) + 1}"
            new_row.setdefault("created_at", "2026-02-15T00:00:00Z")
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


def _headers():
    return {"X-Account-Id": "acct-1"}


def _setup(storage: dict[str, list[dict]], user_id: str):
    app.dependency_overrides[get_supabase] = lambda: FakeSupabaseClient(storage)
    app.dependency_overrides[deps.get_current_user] = lambda: {"id": user_id, "email": f"{user_id}@example.com"}


def test_create_api_key_denies_viewer_and_returns_secret_for_admin():
    storage = {
        "team_members": [
            {"account_id": "acct-1", "user_id": "viewer", "role": "viewer", "status": "accepted", "deleted_at": None},
            {"account_id": "acct-1", "user_id": "admin", "role": "admin", "status": "accepted", "deleted_at": None},
        ],
        "api_keys": [],
    }

    _setup(storage, "viewer")
    try:
        with TestClient(app) as client:
            forbidden = client.post(
                "/v1.0/accounts/acct-1/api-keys",
                headers=_headers(),
                json={"name": "Prod", "scopes": ["read"], "rate_limit_per_hour": 1000},
            )
        assert forbidden.status_code == 403
    finally:
        app.dependency_overrides = {}

    _setup(storage, "admin")
    try:
        with TestClient(app) as client:
            created = client.post(
                "/v1.0/accounts/acct-1/api-keys",
                headers=_headers(),
                json={"name": "Prod", "scopes": ["read"], "rate_limit_per_hour": 1000},
            )

        assert created.status_code == 201
        body = created.json()
        secret = body["data"]["secret"]
        assert secret.startswith("tlm_")
        assert storage["api_keys"][0]["key_hash"] != secret
    finally:
        app.dependency_overrides = {}


def test_rotate_not_found_and_revoke_success():
    storage = {
        "team_members": [
            {"account_id": "acct-1", "user_id": "admin", "role": "admin", "status": "accepted", "deleted_at": None}
        ],
        "api_keys": [
            {
                "id": "key-1",
                "account_id": "acct-1",
                "name": "Prod",
                "key_prefix": "tlm_old_",
                "key_hash": "abc",
                "scopes": ["read"],
                "rate_limit_per_hour": 1000,
                "created_at": "2026-02-15T00:00:00Z",
                "revoked_at": None,
            }
        ],
    }
    _setup(storage, "admin")

    try:
        with TestClient(app) as client:
            not_found = client.post("/v1.0/accounts/acct-1/api-keys/missing/rotate", headers=_headers())
            revoked = client.delete("/v1.0/accounts/acct-1/api-keys/key-1", headers=_headers())

        assert not_found.status_code == 404
        assert revoked.status_code == 204
        assert storage["api_keys"][0]["revoked_at"] is not None
    finally:
        app.dependency_overrides = {}


def test_api_usage_aggregates():
    storage = {
        "team_members": [
            {"account_id": "acct-1", "user_id": "viewer", "role": "viewer", "status": "accepted", "deleted_at": None}
        ],
        "api_keys": [{"id": "key-1", "account_id": "acct-1"}],
        "api_key_usage_daily": [
            {"api_key_id": "key-1", "usage_date": "2026-02-14", "request_count": 100, "error_count": 2, "average_latency_ms": 110},
            {"api_key_id": "key-1", "usage_date": "2026-02-15", "request_count": 50, "error_count": 1, "average_latency_ms": 90},
        ],
    }
    _setup(storage, "viewer")

    try:
        with TestClient(app) as client:
            response = client.get(
                "/v1.0/accounts/acct-1/api-usage?from=2026-02-14&to=2026-02-15",
                headers=_headers(),
            )

        assert response.status_code == 200
        body = response.json()
        assert body["data"]["total_requests"] == 150
        assert len(body["data"]["by_day"]) == 2
    finally:
        app.dependency_overrides = {}
