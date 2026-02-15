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

    def gte(self, field, value):
        self.filters.append(lambda row: str(row.get(field)) >= str(value))
        return self

    def lte(self, field, value):
        self.filters.append(lambda row: str(row.get(field)) <= str(value))
        return self

    def gt(self, field, value):
        self.filters.append(lambda row: str(row.get(field)) > str(value))
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
                new_row["id"] = f"pm-{len(self.storage.get(self.table_name, [])) + 1}"
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


def test_get_subscription_and_invalid_plan_patch():
    storage = {
        "team_members": [
            {"account_id": "acct-1", "user_id": "admin", "role": "admin", "status": "accepted", "deleted_at": None}
        ],
        "account_subscriptions": [
            {
                "id": "sub-1",
                "account_id": "acct-1",
                "plan_id": "plan-pro",
                "status": "active",
                "billing_state": "active",
                "cancel_at_period_end": False,
            }
        ],
        "billing_plans": [{"id": "plan-pro", "code": "pro", "is_active": True}],
    }
    _setup(storage, "admin")

    try:
        with TestClient(app) as client:
            get_resp = client.get("/v1.0/accounts/acct-1/subscription", headers=_headers())
            bad_patch = client.patch(
                "/v1.0/accounts/acct-1/subscription",
                headers=_headers(),
                json={"plan_code": "unknown"},
            )

        assert get_resp.status_code == 200
        assert get_resp.json()["data"]["plan_code"] == "pro"
        assert bad_patch.status_code == 400
    finally:
        app.dependency_overrides = {}


def test_usage_payment_method_and_invoice_download_not_found():
    storage = {
        "team_members": [
            {"account_id": "acct-1", "user_id": "viewer", "role": "viewer", "status": "accepted", "deleted_at": None},
            {"account_id": "acct-1", "user_id": "admin", "role": "admin", "status": "accepted", "deleted_at": None},
        ],
        "account_usage_daily": [
            {
                "account_id": "acct-1",
                "usage_date": "2026-02-14",
                "channel_searches": 10,
                "event_trackers_count": 3,
                "api_requests_count": 40,
                "exports_count": 2,
            }
        ],
        "payment_methods": [],
        "invoices": [],
    }

    _setup(storage, "viewer")
    try:
        with TestClient(app) as client:
            usage_resp = client.get(
                "/v1.0/accounts/acct-1/usage?from=2026-02-14&to=2026-02-14",
                headers=_headers(),
            )
            invalid_pm = client.post(
                "/v1.0/accounts/acct-1/payment-methods",
                headers=_headers(),
                json={"provider_payment_method_token": "bad_token", "make_default": True},
            )
            missing_invoice = client.get(
                "/v1.0/accounts/acct-1/invoices/inv-x/download-url",
                headers=_headers(),
            )

        assert usage_resp.status_code == 200
        assert usage_resp.json()["data"]["channel_searches"] == 10
        assert invalid_pm.status_code == 403
        assert missing_invoice.status_code == 404
    finally:
        app.dependency_overrides = {}

    _setup(storage, "admin")
    try:
        with TestClient(app) as client:
            add_pm = client.post(
                "/v1.0/accounts/acct-1/payment-methods",
                headers=_headers(),
                json={"provider_payment_method_token": "pm_tok_1234", "make_default": True},
            )
        assert add_pm.status_code == 201
        assert len(storage["payment_methods"]) == 1
    finally:
        app.dependency_overrides = {}
