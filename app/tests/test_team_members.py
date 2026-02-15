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
        self.filters: list[callable] = []
        self.action = "select"
        self.update_data: dict | None = None
        self.limit_value: int | None = None

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, field: str, value):
        self.filters.append(lambda row: row.get(field) == value)
        return self

    def is_(self, field: str, value):
        if value == "null":
            self.filters.append(lambda row: row.get(field) is None)
        else:
            self.filters.append(lambda row: row.get(field) == value)
        return self

    def limit(self, count: int):
        self.limit_value = count
        return self

    def update(self, data: dict):
        self.action = "update"
        self.update_data = data
        return self

    def execute(self):
        rows = [
            row
            for row in self.storage.get(self.table_name, [])
            if all(filter_func(row) for filter_func in self.filters)
        ]

        if self.action == "update" and self.update_data is not None:
            updated_rows = []
            for row in self.storage.get(self.table_name, []):
                if all(filter_func(row) for filter_func in self.filters):
                    row.update(self.update_data)
                    updated_rows.append(row.copy())
            return FakeResponse(updated_rows)

        if self.limit_value is not None:
            rows = rows[: self.limit_value]

        return FakeResponse(rows)


class FakeSupabaseClient:
    def __init__(self, storage: dict[str, list[dict]]):
        self.storage = storage

    def table(self, table_name: str):
        return FakeTableQuery(table_name, self.storage)


def _override_current_user():
    return {"id": "user-1", "email": "user@example.com"}


def _get_fake_supabase():
    storage = {
        "users": [
            {"id": "user-1", "email": "user@example.com"},
        ],
        "accounts": [
            {"id": "acct-1", "created_by": "other-user", "is_default": True},
        ],
        "team_members": [
            {
                "id": "tm-1",
                "user_id": "user-1",
                "account_id": "acct-2",
                "role": "guest",
                "status": "accepted",
                "deleted_at": None,
                "deleted_by": None,
                "created_by": "other-user",
            }
        ],
    }
    return FakeSupabaseClient(storage), storage


def test_user_can_remove_own_membership_without_default_account():
    supabase_client, storage = _get_fake_supabase()
    app.dependency_overrides[get_supabase] = lambda: supabase_client
    app.dependency_overrides[deps.get_current_user] = _override_current_user

    try:
        with TestClient(app) as client:
            response = client.delete("/v1.0/team_members/tm-1")

        assert response.status_code == 200
        assert response.json()["message"] == "Team member removed successfully"
        assert storage["team_members"][0]["deleted_at"] is not None
        assert storage["team_members"][0]["deleted_by"] == "user-1"
    finally:
        app.dependency_overrides = {}
