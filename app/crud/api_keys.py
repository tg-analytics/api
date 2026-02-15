from __future__ import annotations

import hashlib
from datetime import UTC, date, datetime, timedelta
from secrets import token_hex
from typing import Any

from supabase import Client


def _to_api_key_list_item(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "api_key_id": row["id"],
        "name": row["name"],
        "key_prefix": row["key_prefix"],
        "scopes": row.get("scopes") or [],
        "rate_limit_per_hour": int(row.get("rate_limit_per_hour") or 0),
        "created_at": row["created_at"],
        "last_used_at": row.get("last_used_at"),
        "revoked_at": row.get("revoked_at"),
    }


def _hash_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def _generate_secret() -> tuple[str, str]:
    prefix = f"tlm_{token_hex(3)}_"
    secret = f"{prefix}{token_hex(24)}"
    return prefix, secret


async def list_api_keys(client: Client, *, account_id: str) -> list[dict[str, Any]]:
    response = (
        client.table("api_keys")
        .select("*")
        .eq("account_id", account_id)
        .order("created_at", desc=True)
        .execute()
    )
    return [_to_api_key_list_item(row) for row in (response.data or [])]


async def create_api_key(
    client: Client,
    *,
    account_id: str,
    user_id: str,
    name: str,
    scopes: list[str],
    rate_limit_per_hour: int,
) -> dict[str, Any]:
    existing = (
        client.table("api_keys")
        .select("id")
        .eq("account_id", account_id)
        .eq("name", name)
        .limit(1)
        .execute()
    )
    if existing.data:
        raise ValueError("API key name already exists in account.")

    key_prefix, secret = _generate_secret()
    payload = {
        "account_id": account_id,
        "name": name,
        "key_prefix": key_prefix,
        "key_hash": _hash_secret(secret),
        "scopes": scopes,
        "rate_limit_per_hour": rate_limit_per_hour,
        "created_by": user_id,
        "updated_by": user_id,
    }
    response = client.table("api_keys").insert(payload).execute()
    if not response.data:
        raise ValueError("Failed to create API key")

    return {
        "api_key": _to_api_key_list_item(response.data[0]),
        "secret": secret,
    }


async def rotate_api_key(
    client: Client,
    *,
    account_id: str,
    api_key_id: str,
    user_id: str,
) -> dict[str, Any] | None:
    existing = (
        client.table("api_keys")
        .select("*")
        .eq("id", api_key_id)
        .eq("account_id", account_id)
        .is_("revoked_at", "null")
        .limit(1)
        .execute()
    )
    if not existing.data:
        return None

    key_prefix, secret = _generate_secret()
    updated = (
        client.table("api_keys")
        .update(
            {
                "key_prefix": key_prefix,
                "key_hash": _hash_secret(secret),
                "updated_by": user_id,
            }
        )
        .eq("id", api_key_id)
        .eq("account_id", account_id)
        .is_("revoked_at", "null")
        .execute()
    )
    if not updated.data:
        return None

    return {
        "api_key": _to_api_key_list_item(updated.data[0]),
        "secret": secret,
    }


async def revoke_api_key(
    client: Client,
    *,
    account_id: str,
    api_key_id: str,
    user_id: str,
) -> bool:
    revoked_at = datetime.now(UTC).isoformat()
    response = (
        client.table("api_keys")
        .update({"revoked_at": revoked_at, "revoked_by": user_id, "updated_by": user_id})
        .eq("id", api_key_id)
        .eq("account_id", account_id)
        .is_("revoked_at", "null")
        .execute()
    )
    return bool(response.data)


async def get_api_usage(
    client: Client,
    *,
    account_id: str,
    from_date: date | None,
    to_date: date | None,
) -> dict[str, Any]:
    today = date.today()
    start = from_date or (today - timedelta(days=29))
    end = to_date or today

    keys = (
        client.table("api_keys")
        .select("id")
        .eq("account_id", account_id)
        .execute()
    ).data or []
    key_ids = [row["id"] for row in keys if row.get("id")]
    if not key_ids:
        return {
            "total_requests": 0,
            "error_rate": 0.0,
            "avg_latency_ms": 0.0,
            "by_day": [],
        }

    usage_query = (
        client.table("api_key_usage_daily")
        .select("usage_date, request_count, error_count, average_latency_ms")
        .in_("api_key_id", key_ids)
        .gte("usage_date", start.isoformat())
        .lte("usage_date", end.isoformat())
    )
    usage_rows = usage_query.execute().data or []

    per_day: dict[str, dict[str, int]] = {}
    total_requests = 0
    total_errors = 0
    weighted_latency_sum = 0.0
    latency_weight = 0

    for row in usage_rows:
        day = str(row["usage_date"])
        requests = int(row.get("request_count") or 0)
        errors = int(row.get("error_count") or 0)
        latency = row.get("average_latency_ms")

        total_requests += requests
        total_errors += errors

        if latency is not None and requests > 0:
            weighted_latency_sum += float(latency) * requests
            latency_weight += requests

        if day not in per_day:
            per_day[day] = {"requests": 0, "errors": 0}
        per_day[day]["requests"] += requests
        per_day[day]["errors"] += errors

    by_day = [
        {"date": day, "requests": values["requests"], "errors": values["errors"]}
        for day, values in sorted(per_day.items(), key=lambda item: item[0])
    ]

    return {
        "total_requests": total_requests,
        "error_rate": round((total_errors / total_requests) * 100, 4) if total_requests > 0 else 0.0,
        "avg_latency_ms": round(weighted_latency_sum / latency_weight, 4) if latency_weight > 0 else 0.0,
        "by_day": by_day,
    }
