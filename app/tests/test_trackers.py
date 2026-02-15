from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi.testclient import TestClient
from postgrest.exceptions import APIError

from app.api import deps
from app.db.base import get_supabase
from app.main import app


class FakeResponse:
    def __init__(self, data: list[dict[str, Any]], count: int | None = None):
        self.data = data
        self.count = count


class FakeTableQuery:
    def __init__(self, table_name: str, storage: dict[str, list[dict[str, Any]]]):
        self.table_name = table_name
        self.storage = storage
        self.filters: list = []
        self.orders: list[tuple[str, bool]] = []
        self.limit_value: int | None = None
        self.action = "select"
        self.insert_data: dict[str, Any] | None = None
        self.update_data: dict[str, Any] | None = None

    def select(self, *_args, **_kwargs):
        self.action = "select"
        return self

    def insert(self, data: dict[str, Any]):
        self.action = "insert"
        self.insert_data = data
        return self

    def update(self, data: dict[str, Any]):
        self.action = "update"
        self.update_data = data
        return self

    def eq(self, field: str, value: Any):
        self.filters.append(lambda row: row.get(field) == value)
        return self

    def is_(self, field: str, value: Any):
        if value == "null":
            self.filters.append(lambda row: row.get(field) is None)
        else:
            self.filters.append(lambda row: row.get(field) == value)
        return self

    def in_(self, field: str, values: list[Any]):
        allowed = set(values)
        self.filters.append(lambda row: row.get(field) in allowed)
        return self

    def gte(self, field: str, value: Any):
        self.filters.append(lambda row: _coerce_value(row.get(field)) >= _coerce_value(value))
        return self

    def lte(self, field: str, value: Any):
        self.filters.append(lambda row: _coerce_value(row.get(field)) <= _coerce_value(value))
        return self

    def lt(self, field: str, value: Any):
        self.filters.append(lambda row: _coerce_value(row.get(field)) < _coerce_value(value))
        return self

    def order(self, field: str, desc: bool = False, **_kwargs):
        self.orders.append((field, desc))
        return self

    def limit(self, count: int):
        self.limit_value = count
        return self

    def _matches(self, row: dict[str, Any]) -> bool:
        return all(predicate(row) for predicate in self.filters)

    def execute(self) -> FakeResponse:
        if self.action == "insert":
            return self._execute_insert()

        if self.action == "update":
            return self._execute_update()

        rows = [row.copy() for row in self.storage.get(self.table_name, []) if self._matches(row)]

        for field, desc in reversed(self.orders):
            non_null = [row for row in rows if row.get(field) is not None]
            null_rows = [row for row in rows if row.get(field) is None]
            non_null.sort(key=lambda row: _coerce_value(row.get(field)), reverse=desc)
            rows = non_null + null_rows

        if self.limit_value is not None:
            rows = rows[: self.limit_value]

        return FakeResponse(rows)

    def _execute_insert(self) -> FakeResponse:
        assert self.insert_data is not None
        new_row = self.insert_data.copy()

        if self.table_name == "trackers":
            for row in self.storage["trackers"]:
                if (
                    row.get("deleted_at") is None
                    and row.get("account_id") == new_row.get("account_id")
                    and row.get("tracker_type") == new_row.get("tracker_type")
                    and row.get("normalized_value") == new_row.get("normalized_value")
                ):
                    raise APIError(
                        {
                            "message": "duplicate key value violates unique constraint",
                            "code": "23505",
                            "details": "",
                            "hint": "",
                        }
                    )

            now = datetime.now(UTC).isoformat()
            next_id = f"00000000-0000-0000-0000-{len(self.storage['trackers']) + 1000:012d}"
            new_row.setdefault("id", next_id)
            new_row.setdefault("status", "active")
            new_row.setdefault("mentions_count", 0)
            new_row.setdefault("last_activity_at", None)
            new_row.setdefault("paused_at", None)
            new_row.setdefault("created_at", now)
            new_row.setdefault("updated_at", now)
            new_row.setdefault("deleted_at", None)
            new_row.setdefault("deleted_by", None)

        self.storage[self.table_name].append(new_row)
        return FakeResponse([new_row.copy()])

    def _execute_update(self) -> FakeResponse:
        assert self.update_data is not None
        updated: list[dict[str, Any]] = []

        for row in self.storage.get(self.table_name, []):
            if self._matches(row):
                row.update(self.update_data)
                if self.table_name == "trackers":
                    row["updated_at"] = datetime.now(UTC).isoformat()
                updated.append(row.copy())

        return FakeResponse(updated)


class FakeSupabaseClient:
    def __init__(self, storage: dict[str, list[dict[str, Any]]]):
        self.storage = storage

    def table(self, table_name: str):
        return FakeTableQuery(table_name, self.storage)


def _coerce_value(value: Any) -> Any:
    if value is None:
        return value

    if isinstance(value, datetime):
        return value

    if isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            pass

    return value


def _seed_storage() -> dict[str, list[dict[str, Any]]]:
    account_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    another_account = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    tracker_1 = "11111111-1111-1111-1111-111111111111"
    tracker_2 = "22222222-2222-2222-2222-222222222222"

    return {
        "team_members": [
            {
                "id": "tm-1",
                "account_id": account_id,
                "user_id": "user-editor",
                "role": "editor",
                "status": "accepted",
                "deleted_at": None,
            },
            {
                "id": "tm-2",
                "account_id": account_id,
                "user_id": "user-viewer",
                "role": "viewer",
                "status": "accepted",
                "deleted_at": None,
            },
        ],
        "trackers": [
            {
                "id": tracker_1,
                "account_id": account_id,
                "tracker_type": "keyword",
                "tracker_value": "bitcoin price",
                "normalized_value": "bitcoin price",
                "status": "active",
                "mentions_count": 3,
                "last_activity_at": "2026-02-14T12:00:00Z",
                "notify_push": True,
                "notify_telegram": True,
                "notify_email": False,
                "created_by": "user-editor",
                "updated_by": "user-editor",
                "updated_at": "2026-02-14T12:01:00Z",
                "deleted_at": None,
                "deleted_by": None,
            },
            {
                "id": tracker_2,
                "account_id": account_id,
                "tracker_type": "channel",
                "tracker_value": "@technewsdaily",
                "normalized_value": "@technewsdaily",
                "status": "paused",
                "mentions_count": 2,
                "last_activity_at": "2026-02-14T09:00:00Z",
                "notify_push": True,
                "notify_telegram": True,
                "notify_email": True,
                "created_by": "user-editor",
                "updated_by": "user-editor",
                "updated_at": "2026-02-14T09:00:00Z",
                "deleted_at": None,
                "deleted_by": None,
            },
            {
                "id": "33333333-3333-3333-3333-333333333333",
                "account_id": another_account,
                "tracker_type": "keyword",
                "tracker_value": "ethereum",
                "normalized_value": "ethereum",
                "status": "active",
                "mentions_count": 1,
                "last_activity_at": "2026-02-14T07:00:00Z",
                "notify_push": True,
                "notify_telegram": True,
                "notify_email": False,
                "created_by": "user-editor",
                "updated_by": "user-editor",
                "updated_at": "2026-02-14T07:00:00Z",
                "deleted_at": None,
                "deleted_by": None,
            },
        ],
        "tracker_mentions": [
            {
                "id": "m-1",
                "account_id": account_id,
                "tracker_id": tracker_1,
                "mention_seq": 1003,
                "channel_id": "ch-1",
                "post_id": "p-1",
                "mention_text": "bitcoin price",
                "context_snippet": "Bitcoin price rallied",
                "mentioned_at": "2026-02-14T21:00:00Z",
            },
            {
                "id": "m-2",
                "account_id": account_id,
                "tracker_id": tracker_1,
                "mention_seq": 1002,
                "channel_id": "ch-2",
                "post_id": "p-2",
                "mention_text": "bitcoin price",
                "context_snippet": "price update",
                "mentioned_at": "2026-02-14T20:00:00Z",
            },
            {
                "id": "m-3",
                "account_id": account_id,
                "tracker_id": tracker_2,
                "mention_seq": 1001,
                "channel_id": None,
                "post_id": None,
                "mention_text": "@technewsdaily",
                "context_snippet": None,
                "mentioned_at": "2026-02-14T19:00:00Z",
            },
        ],
        "channels": [
            {"id": "ch-1", "name": "Tech News Daily"},
            {"id": "ch-2", "name": "Crypto Radar"},
        ],
    }


def _override_user(user_id: str):
    def _provider() -> dict[str, str]:
        return {"id": user_id, "email": f"{user_id}@example.com"}

    return _provider


def _setup(user_id: str):
    storage = _seed_storage()
    client = FakeSupabaseClient(storage)
    app.dependency_overrides[get_supabase] = lambda: client
    app.dependency_overrides[deps.get_current_user] = _override_user(user_id)
    return storage


def _headers(account_id: str = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa") -> dict[str, str]:
    return {"X-Account-Id": account_id}


def test_get_trackers_base_list():
    _setup("user-editor")
    try:
        with TestClient(app) as client:
            response = client.get(
                "/v1.0/accounts/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/trackers",
                headers=_headers(),
            )

        assert response.status_code == 200
        body = response.json()
        assert len(body["data"]) == 2
        assert body["data"][0]["tracker_id"] == "11111111-1111-1111-1111-111111111111"
    finally:
        app.dependency_overrides = {}


def test_get_trackers_filter_by_status_and_type():
    _setup("user-editor")
    try:
        with TestClient(app) as client:
            response = client.get(
                "/v1.0/accounts/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/trackers?status=active&type=keyword",
                headers=_headers(),
            )

        assert response.status_code == 200
        body = response.json()
        assert len(body["data"]) == 1
        assert body["data"][0]["tracker_type"] == "keyword"
    finally:
        app.dependency_overrides = {}


def test_get_tracker_by_id_success():
    _setup("user-editor")
    try:
        with TestClient(app) as client:
            response = client.get(
                "/v1.0/accounts/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/trackers/11111111-1111-1111-1111-111111111111",
                headers=_headers(),
            )

        assert response.status_code == 200
        body = response.json()
        assert body["data"]["tracker_id"] == "11111111-1111-1111-1111-111111111111"
        assert body["data"]["tracker_type"] == "keyword"
    finally:
        app.dependency_overrides = {}


def test_get_tracker_by_id_not_found_returns_404():
    _setup("user-editor")
    try:
        with TestClient(app) as client:
            response = client.get(
                "/v1.0/accounts/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/trackers/99999999-9999-9999-9999-999999999999",
                headers=_headers(),
            )

        assert response.status_code == 404
        assert response.json()["detail"] == "Tracker not found."
    finally:
        app.dependency_overrides = {}


def test_post_tracker_success_created_201():
    storage = _setup("user-editor")
    try:
        with TestClient(app) as client:
            response = client.post(
                "/v1.0/accounts/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/trackers",
                headers=_headers(),
                json={
                    "tracker_type": "keyword",
                    "tracker_value": "solana",
                    "notify_push": True,
                    "notify_telegram": False,
                    "notify_email": True,
                },
            )

        assert response.status_code == 201
        body = response.json()
        assert body["data"]["tracker_value"] == "solana"
        assert any(row["normalized_value"] == "solana" for row in storage["trackers"])
    finally:
        app.dependency_overrides = {}


def test_post_tracker_duplicate_returns_400():
    _setup("user-editor")
    try:
        with TestClient(app) as client:
            response = client.post(
                "/v1.0/accounts/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/trackers",
                headers=_headers(),
                json={"tracker_type": "keyword", "tracker_value": "bitcoin price"},
            )

        assert response.status_code == 400
        assert response.json()["detail"] == "Tracker already exists for this account."
    finally:
        app.dependency_overrides = {}


def test_patch_tracker_success_updates_fields():
    _setup("user-editor")
    try:
        with TestClient(app) as client:
            response = client.patch(
                "/v1.0/accounts/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/trackers/11111111-1111-1111-1111-111111111111",
                headers=_headers(),
                json={"status": "paused", "notify_push": False},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["data"]["status"] == "paused"
        assert body["data"]["notify_push"] is False
    finally:
        app.dependency_overrides = {}


def test_patch_tracker_forbidden_for_viewer():
    _setup("user-viewer")
    try:
        with TestClient(app) as client:
            response = client.patch(
                "/v1.0/accounts/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/trackers/11111111-1111-1111-1111-111111111111",
                headers=_headers(),
                json={"status": "paused"},
            )

        assert response.status_code == 403
    finally:
        app.dependency_overrides = {}


def test_patch_tracker_not_found_returns_404():
    _setup("user-editor")
    try:
        with TestClient(app) as client:
            response = client.patch(
                "/v1.0/accounts/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/trackers/99999999-9999-9999-9999-999999999999",
                headers=_headers(),
                json={"status": "active"},
            )

        assert response.status_code == 404
    finally:
        app.dependency_overrides = {}


def test_delete_tracker_success_204():
    storage = _setup("user-editor")
    try:
        with TestClient(app) as client:
            response = client.delete(
                "/v1.0/accounts/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/trackers/11111111-1111-1111-1111-111111111111",
                headers=_headers(),
            )

        assert response.status_code == 204
        deleted = next(
            row for row in storage["trackers"] if row["id"] == "11111111-1111-1111-1111-111111111111"
        )
        assert deleted["deleted_at"] is not None
    finally:
        app.dependency_overrides = {}


def test_delete_tracker_not_found_returns_404():
    _setup("user-editor")
    try:
        with TestClient(app) as client:
            response = client.delete(
                "/v1.0/accounts/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/trackers/99999999-9999-9999-9999-999999999999",
                headers=_headers(),
            )

        assert response.status_code == 404
    finally:
        app.dependency_overrides = {}


def test_get_tracker_mentions_base_polling():
    _setup("user-editor")
    try:
        with TestClient(app) as client:
            response = client.get(
                "/v1.0/accounts/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/tracker-mentions?limit=2",
                headers=_headers(),
            )

        assert response.status_code == 200
        body = response.json()
        assert len(body["data"]) == 2
        assert body["page"]["has_more"] is True
        assert body["data"][0]["channel_name"] == "Tech News Daily"
    finally:
        app.dependency_overrides = {}


def test_get_tracker_mentions_cursor_next_page():
    _setup("user-editor")
    try:
        with TestClient(app) as client:
            first = client.get(
                "/v1.0/accounts/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/tracker-mentions?limit=2",
                headers=_headers(),
            )
            cursor = first.json()["page"]["next_cursor"]
            second = client.get(
                f"/v1.0/accounts/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/tracker-mentions?limit=2&cursor={cursor}",
                headers=_headers(),
            )

        assert second.status_code == 200
        body = second.json()
        assert len(body["data"]) == 1
        assert body["data"][0]["mention_seq"] == 1001
    finally:
        app.dependency_overrides = {}


def test_get_tracker_mentions_filters_tracker_and_time_range():
    _setup("user-editor")
    try:
        with TestClient(app) as client:
            response = client.get(
                "/v1.0/accounts/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/tracker-mentions"
                "?tracker_id=11111111-1111-1111-1111-111111111111"
                "&since=2026-02-14T20:30:00Z&until=2026-02-14T21:30:00Z",
                headers=_headers(),
            )

        assert response.status_code == 200
        body = response.json()
        assert len(body["data"]) == 1
        assert body["data"][0]["mention_seq"] == 1003
    finally:
        app.dependency_overrides = {}


def test_get_tracker_mentions_invalid_cursor_returns_400():
    _setup("user-editor")
    try:
        with TestClient(app) as client:
            response = client.get(
                "/v1.0/accounts/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/tracker-mentions?cursor=bad-cursor",
                headers=_headers(),
            )

        assert response.status_code == 400
    finally:
        app.dependency_overrides = {}


def test_header_path_mismatch_returns_403():
    _setup("user-editor")
    try:
        with TestClient(app) as client:
            response = client.get(
                "/v1.0/accounts/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/trackers",
                headers=_headers("cccccccc-cccc-cccc-cccc-cccccccccccc"),
            )

        assert response.status_code == 403
    finally:
        app.dependency_overrides = {}


def test_non_member_returns_403():
    _setup("user-non-member")
    try:
        with TestClient(app) as client:
            response = client.get(
                "/v1.0/accounts/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/trackers",
                headers=_headers(),
            )

        assert response.status_code == 403
    finally:
        app.dependency_overrides = {}


def test_unauthorized_returns_401():
    storage = _seed_storage()
    app.dependency_overrides[get_supabase] = lambda: FakeSupabaseClient(storage)

    try:
        with TestClient(app) as client:
            response = client.get(
                "/v1.0/accounts/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/trackers",
                headers=_headers(),
            )

        assert response.status_code == 401
    finally:
        app.dependency_overrides = {}
