from __future__ import annotations

import base64
import json

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
        self.orders: list[tuple[str, bool]] = []
        self.limit_value: int | None = None
        self.action = "select"
        self.payload = None

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

    def gt(self, field, value):
        self.filters.append(lambda row: row.get(field) is not None and row.get(field) > value)
        return self

    def in_(self, field, values):
        allowed = set(values)
        self.filters.append(lambda row: row.get(field) in allowed)
        return self

    def order(self, field: str, desc: bool = False, **_kwargs):
        self.orders.append((field, desc))
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
            rows = [row.copy() for row in rows]
            for field, desc in reversed(self.orders):
                rows.sort(key=lambda row: row.get(field), reverse=desc)
            if self.limit_value is not None:
                rows = rows[: self.limit_value]
            return FakeResponse(rows)

        if self.action == "insert":
            new_row = self.payload.copy()
            if "id" not in new_row:
                new_row["id"] = f"id-{len(self.storage.get(self.table_name, [])) + 1}"
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


def _headers(account_id: str = "acct-1"):
    return {"X-Account-Id": account_id}


def _setup(storage: dict[str, list[dict]], user_id: str):
    app.dependency_overrides[get_supabase] = lambda: FakeSupabaseClient(storage)
    app.dependency_overrides[deps.get_current_user] = lambda: {"id": user_id, "email": f"{user_id}@example.com"}


def _cursor_for_channel(channel_id: str) -> str:
    return base64.urlsafe_b64encode(json.dumps({"channel_id": channel_id}).encode()).decode()


def test_get_channels_allows_accepted_member_and_paginates():
    storage = {
        "team_members": [
            {"account_id": "acct-1", "user_id": "viewer", "role": "viewer", "status": "accepted", "deleted_at": None}
        ],
        "account_channels": [
            {"account_id": "acct-1", "channel_id": "ch-1", "alias_name": None, "monitoring_enabled": True, "is_favorite": False, "created_at": "2026-02-15T00:00:00Z", "deleted_at": None},
            {"account_id": "acct-1", "channel_id": "ch-2", "alias_name": None, "monitoring_enabled": True, "is_favorite": False, "created_at": "2026-02-15T00:01:00Z", "deleted_at": None},
        ],
    }
    _setup(storage, "viewer")

    try:
        with TestClient(app) as client:
            response = client.get("/v1.0/accounts/acct-1/channels?limit=1", headers=_headers())

        assert response.status_code == 200
        body = response.json()
        assert len(body["data"]) == 1
        assert body["page"]["has_more"] is True
        assert body["page"]["next_cursor"] is not None
    finally:
        app.dependency_overrides = {}


def test_post_channel_denies_viewer_and_allows_admin():
    storage = {
        "team_members": [
            {"account_id": "acct-1", "user_id": "viewer", "role": "viewer", "status": "accepted", "deleted_at": None},
            {"account_id": "acct-1", "user_id": "admin", "role": "admin", "status": "accepted", "deleted_at": None},
        ],
        "account_channels": [],
    }

    _setup(storage, "viewer")
    try:
        with TestClient(app) as client:
            forbidden = client.post(
                "/v1.0/accounts/acct-1/channels",
                headers=_headers(),
                json={"channel_id": "ch-9"},
            )
        assert forbidden.status_code == 403
    finally:
        app.dependency_overrides = {}

    _setup(storage, "admin")
    try:
        with TestClient(app) as client:
            created = client.post(
                "/v1.0/accounts/acct-1/channels",
                headers=_headers(),
                json={"channel_id": "ch-9", "is_favorite": True},
            )
        assert created.status_code == 201
        assert created.json()["data"]["channel_id"] == "ch-9"
    finally:
        app.dependency_overrides = {}


def test_verification_create_and_confirm_expired_error():
    storage = {
        "team_members": [
            {"account_id": "acct-1", "user_id": "admin", "role": "admin", "status": "accepted", "deleted_at": None}
        ],
        "channel_verification_requests": [
            {
                "id": "req-expired",
                "account_id": "acct-1",
                "channel_id": "ch-1",
                "verification_code": "TP-OLD",
                "verification_method": "description_code",
                "status": "pending",
                "requested_at": "2026-01-01T00:00:00Z",
                "expires_at": "2026-01-02T00:00:00Z",
            }
        ],
        "account_channels": [],
        "channels": [],
    }
    _setup(storage, "admin")

    try:
        with TestClient(app) as client:
            create_resp = client.post(
                "/v1.0/accounts/acct-1/channels/ch-2/verification",
                headers=_headers(),
                json={"verification_method": "description_code"},
            )
            confirm_resp = client.post(
                "/v1.0/accounts/acct-1/channels/ch-1/verification/req-expired/confirm",
                headers=_headers(),
                json={"evidence": {"ok": True}},
            )

        assert create_resp.status_code == 201
        assert confirm_resp.status_code == 400
        assert "expired" in confirm_resp.json()["detail"].lower()
    finally:
        app.dependency_overrides = {}
