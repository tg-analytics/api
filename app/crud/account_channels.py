from __future__ import annotations

import json
from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import UTC, datetime, timedelta
from secrets import token_hex
from typing import Any

from supabase import Client


def _encode_cursor(last_channel_id: str) -> str:
    payload = json.dumps({"channel_id": last_channel_id}).encode("utf-8")
    return urlsafe_b64encode(payload).decode("utf-8")


def _decode_cursor(cursor: str) -> str:
    try:
        payload = json.loads(urlsafe_b64decode(cursor).decode("utf-8"))
        channel_id = str(payload["channel_id"])
    except Exception as exc:  # noqa: BLE001
        raise ValueError("Invalid pagination cursor") from exc
    if not channel_id:
        raise ValueError("Invalid pagination cursor")
    return channel_id


def _to_account_channel(row: dict[str, Any]) -> dict[str, Any]:
    added_at = row.get("created_at") or datetime.now(UTC).isoformat()
    return {
        "account_id": row["account_id"],
        "channel_id": row["channel_id"],
        "alias_name": row.get("alias_name"),
        "monitoring_enabled": bool(row.get("monitoring_enabled", True)),
        "is_favorite": bool(row.get("is_favorite", False)),
        "added_at": added_at,
    }


def _to_verification_request(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "request_id": row["id"],
        "account_id": row["account_id"],
        "channel_id": row["channel_id"],
        "verification_code": row["verification_code"],
        "verification_method": row["verification_method"],
        "status": row["status"],
        "requested_at": row["requested_at"],
        "confirmed_at": row.get("confirmed_at"),
        "expires_at": row["expires_at"],
    }


async def list_account_channels(
    client: Client,
    *,
    account_id: str,
    limit: int,
    cursor: str | None,
) -> dict[str, Any]:
    query = (
        client.table("account_channels")
        .select("*")
        .eq("account_id", account_id)
        .is_("deleted_at", "null")
        .order("channel_id", desc=False)
    )

    if cursor:
        query = query.gt("channel_id", _decode_cursor(cursor))

    response = query.limit(limit + 1).execute()
    rows = response.data or []

    has_more = len(rows) > limit
    page_rows = rows[:limit]
    next_cursor = _encode_cursor(page_rows[-1]["channel_id"]) if has_more and page_rows else None

    return {
        "items": [_to_account_channel(row) for row in page_rows],
        "next_cursor": next_cursor,
        "has_more": has_more,
    }


async def add_account_channel(
    client: Client,
    *,
    account_id: str,
    user_id: str,
    channel_id: str,
    alias_name: str | None,
    monitoring_enabled: bool,
    is_favorite: bool,
) -> dict[str, Any]:
    existing = (
        client.table("account_channels")
        .select("account_id, channel_id")
        .eq("account_id", account_id)
        .eq("channel_id", channel_id)
        .is_("deleted_at", "null")
        .limit(1)
        .execute()
    )
    if existing.data:
        raise ValueError("Channel already exists in account.")

    payload = {
        "account_id": account_id,
        "channel_id": channel_id,
        "alias_name": alias_name,
        "monitoring_enabled": monitoring_enabled,
        "is_favorite": is_favorite,
        "created_by": user_id,
        "updated_by": user_id,
    }
    response = client.table("account_channels").insert(payload).execute()
    if not response.data:
        raise ValueError("Failed to add channel")
    return _to_account_channel(response.data[0])


async def get_account_channel_insights(client: Client, *, account_id: str) -> dict[str, Any]:
    account_channels = (
        client.table("account_channels")
        .select("channel_id")
        .eq("account_id", account_id)
        .is_("deleted_at", "null")
        .execute()
    ).data or []

    channel_ids = [row["channel_id"] for row in account_channels if row.get("channel_id")]
    if not channel_ids:
        return {
            "total_subscribers": 0,
            "total_views": 0,
            "avg_engagement_rate": 0.0,
            "channels_count": 0,
        }

    channel_rows = (
        client.table("channels")
        .select("id, subscribers_current, avg_views_current, engagement_rate_current")
        .in_("id", channel_ids)
        .execute()
    ).data or []

    total_subscribers = sum(int(row.get("subscribers_current") or 0) for row in channel_rows)
    total_views = sum(int(row.get("avg_views_current") or 0) for row in channel_rows)
    er_values = [float(row["engagement_rate_current"]) for row in channel_rows if row.get("engagement_rate_current") is not None]
    avg_er = sum(er_values) / len(er_values) if er_values else 0.0

    return {
        "total_subscribers": total_subscribers,
        "total_views": total_views,
        "avg_engagement_rate": round(avg_er, 4),
        "channels_count": len(channel_rows),
    }


async def create_verification_request(
    client: Client,
    *,
    account_id: str,
    channel_id: str,
    user_id: str,
    verification_method: str,
) -> dict[str, Any]:
    existing_pending = (
        client.table("channel_verification_requests")
        .select("id")
        .eq("account_id", account_id)
        .eq("channel_id", channel_id)
        .eq("status", "pending")
        .limit(1)
        .execute()
    )
    if existing_pending.data:
        raise ValueError("Pending verification already exists for this channel.")

    now = datetime.now(UTC)
    payload = {
        "account_id": account_id,
        "channel_id": channel_id,
        "verification_code": f"TP-{token_hex(4).upper()}",
        "verification_method": verification_method,
        "status": "pending",
        "requested_by": user_id,
        "requested_at": now.isoformat(),
        "expires_at": (now + timedelta(days=7)).isoformat(),
    }

    response = client.table("channel_verification_requests").insert(payload).execute()
    if not response.data:
        raise ValueError("Failed to create verification request")

    return _to_verification_request(response.data[0])


async def confirm_verification_request(
    client: Client,
    *,
    account_id: str,
    channel_id: str,
    request_id: str,
    user_id: str,
    evidence: dict[str, object],
) -> dict[str, Any] | None:
    response = (
        client.table("channel_verification_requests")
        .select("*")
        .eq("id", request_id)
        .eq("account_id", account_id)
        .eq("channel_id", channel_id)
        .limit(1)
        .execute()
    )
    if not response.data:
        return None

    row = response.data[0]
    if row.get("status") != "pending":
        raise ValueError("Verification request is not pending.")

    expires_at_raw = row.get("expires_at")
    if expires_at_raw:
        expires_at = datetime.fromisoformat(str(expires_at_raw).replace("Z", "+00:00"))
        if datetime.now(UTC) > expires_at:
            raise ValueError("Verification request expired.")

    update_payload = {
        "status": "confirmed",
        "confirmed_at": datetime.now(UTC).isoformat(),
        "confirmed_by": user_id,
        "evidence": evidence or {},
    }
    updated = (
        client.table("channel_verification_requests")
        .update(update_payload)
        .eq("id", request_id)
        .eq("account_id", account_id)
        .eq("channel_id", channel_id)
        .execute()
    )

    if not updated.data:
        return None
    return _to_verification_request(updated.data[0])
