import json
from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import UTC, datetime
from typing import Any

from postgrest.exceptions import APIError
from supabase import Client

from app.schemas.tracker import TrackerStatus, TrackerType

_WRITE_ROLES = {"owner", "admin", "editor"}


def _encode_mentions_cursor(mention_seq: int) -> str:
    payload = {"mention_seq": mention_seq}
    raw = json.dumps(payload).encode("utf-8")
    return urlsafe_b64encode(raw).decode("utf-8")


def _decode_mentions_cursor(cursor: str) -> dict[str, Any]:
    try:
        raw = urlsafe_b64decode(cursor).decode("utf-8")
        payload = json.loads(raw)
    except Exception as exc:  # noqa: BLE001
        raise ValueError("Invalid pagination cursor") from exc

    if not isinstance(payload, dict) or "mention_seq" not in payload:
        raise ValueError("Invalid pagination cursor")

    try:
        mention_seq = int(payload["mention_seq"])
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid pagination cursor") from exc

    if mention_seq <= 0:
        raise ValueError("Invalid pagination cursor")

    return {"mention_seq": mention_seq}


def _normalize_tracker_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "tracker_id": row["id"],
        "account_id": row["account_id"],
        "tracker_type": row["tracker_type"],
        "tracker_value": row["tracker_value"],
        "status": row["status"],
        "mentions_count": int(row.get("mentions_count") or 0),
        "last_activity_at": row.get("last_activity_at"),
        "notify_push": bool(row.get("notify_push", True)),
        "notify_telegram": bool(row.get("notify_telegram", True)),
        "notify_email": bool(row.get("notify_email", False)),
    }


async def get_account_membership_role(client: Client, account_id: str, user_id: str) -> str | None:
    response = (
        client.table("team_members")
        .select("role")
        .eq("account_id", account_id)
        .eq("user_id", user_id)
        .eq("status", "accepted")
        .is_("deleted_at", "null")
        .limit(1)
        .execute()
    )
    if not response.data:
        return None
    role = response.data[0].get("role")
    if role is None:
        return None
    return str(role).lower()


async def ensure_account_access(
    client: Client,
    *,
    account_id: str,
    header_account_id: str,
    user_id: str,
    require_write: bool = False,
) -> str:
    if account_id != header_account_id:
        raise PermissionError("X-Account-Id must match accountId path parameter")

    role = await get_account_membership_role(client, account_id, user_id)
    if role is None:
        raise PermissionError("You are not a member of this account")

    if require_write and role not in _WRITE_ROLES:
        raise PermissionError("Insufficient permissions to update tracker.")

    return role


async def list_trackers(
    client: Client,
    *,
    account_id: str,
    status: TrackerStatus | None = None,
    tracker_type: TrackerType | None = None,
) -> list[dict[str, Any]]:
    query = (
        client.table("trackers")
        .select("*")
        .eq("account_id", account_id)
        .is_("deleted_at", "null")
    )

    if status is not None:
        query = query.eq("status", status.value)

    if tracker_type is not None:
        query = query.eq("tracker_type", tracker_type.value)

    response = query.order("updated_at", desc=True).order("id", desc=True).execute()
    return [_normalize_tracker_row(row) for row in (response.data or [])]


async def get_tracker(
    client: Client,
    *,
    account_id: str,
    tracker_id: str,
) -> dict[str, Any] | None:
    response = (
        client.table("trackers")
        .select("*")
        .eq("account_id", account_id)
        .eq("id", tracker_id)
        .is_("deleted_at", "null")
        .limit(1)
        .execute()
    )
    if not response.data:
        return None

    return _normalize_tracker_row(response.data[0])


async def create_tracker(
    client: Client,
    *,
    account_id: str,
    user_id: str,
    tracker_type: TrackerType,
    tracker_value: str,
    notify_push: bool,
    notify_telegram: bool,
    notify_email: bool,
) -> dict[str, Any]:
    normalized_value = tracker_value.strip().lower()
    payload = {
        "account_id": account_id,
        "tracker_type": tracker_type.value,
        "tracker_value": tracker_value.strip(),
        "normalized_value": normalized_value,
        "notify_push": notify_push,
        "notify_telegram": notify_telegram,
        "notify_email": notify_email,
        "created_by": user_id,
        "updated_by": user_id,
    }

    try:
        response = client.table("trackers").insert(payload).execute()
    except APIError as exc:
        message = str(exc)
        if "duplicate key" in message.lower() or "normalized_value" in message:
            raise ValueError("Tracker already exists for this account.") from exc
        raise

    if not response.data:
        raise ValueError("Failed to create tracker")

    return _normalize_tracker_row(response.data[0])


async def update_tracker(
    client: Client,
    *,
    account_id: str,
    tracker_id: str,
    user_id: str,
    status: TrackerStatus | None,
    notify_push: bool | None,
    notify_telegram: bool | None,
    notify_email: bool | None,
) -> dict[str, Any] | None:
    existing_response = (
        client.table("trackers")
        .select("*")
        .eq("id", tracker_id)
        .eq("account_id", account_id)
        .is_("deleted_at", "null")
        .limit(1)
        .execute()
    )
    if not existing_response.data:
        return None

    existing = existing_response.data[0]
    update_payload: dict[str, Any] = {"updated_by": user_id}

    if status is not None:
        update_payload["status"] = status.value
        if status == TrackerStatus.PAUSED:
            update_payload["paused_at"] = datetime.now(UTC).isoformat()
        elif existing.get("status") == TrackerStatus.PAUSED.value:
            update_payload["paused_at"] = None

    if notify_push is not None:
        update_payload["notify_push"] = notify_push
    if notify_telegram is not None:
        update_payload["notify_telegram"] = notify_telegram
    if notify_email is not None:
        update_payload["notify_email"] = notify_email

    response = (
        client.table("trackers")
        .update(update_payload)
        .eq("id", tracker_id)
        .eq("account_id", account_id)
        .is_("deleted_at", "null")
        .execute()
    )
    if not response.data:
        return None

    return _normalize_tracker_row(response.data[0])


async def delete_tracker(
    client: Client,
    *,
    account_id: str,
    tracker_id: str,
    user_id: str,
) -> bool:
    payload = {
        "deleted_at": datetime.now(UTC).isoformat(),
        "deleted_by": user_id,
        "updated_by": user_id,
    }

    response = (
        client.table("trackers")
        .update(payload)
        .eq("id", tracker_id)
        .eq("account_id", account_id)
        .is_("deleted_at", "null")
        .execute()
    )

    return bool(response.data)


async def list_tracker_mentions(
    client: Client,
    *,
    account_id: str,
    tracker_id: str | None,
    since: datetime | None,
    until: datetime | None,
    limit: int,
    cursor: str | None,
) -> dict[str, Any]:
    query = client.table("tracker_mentions").select("*").eq("account_id", account_id)

    if tracker_id is not None:
        query = query.eq("tracker_id", tracker_id)

    if since is not None:
        query = query.gte("mentioned_at", since.isoformat())

    if until is not None:
        query = query.lte("mentioned_at", until.isoformat())

    if cursor:
        payload = _decode_mentions_cursor(cursor)
        query = query.lt("mention_seq", payload["mention_seq"])

    rows = query.order("mention_seq", desc=True).limit(limit + 1).execute().data or []

    has_more = len(rows) > limit
    page_rows = rows[:limit]

    channel_ids = list({row.get("channel_id") for row in page_rows if row.get("channel_id")})
    channel_name_map: dict[str, str] = {}
    if channel_ids:
        channel_rows = (
            client.table("channels")
            .select("id,name")
            .in_("id", channel_ids)
            .execute()
            .data
            or []
        )
        channel_name_map = {
            str(channel["id"]): str(channel.get("name"))
            for channel in channel_rows
            if channel.get("id") is not None
        }

    items: list[dict[str, Any]] = []
    for row in page_rows:
        channel_id = row.get("channel_id")
        items.append(
            {
                "mention_id": row["id"],
                "tracker_id": row["tracker_id"],
                "mention_seq": int(row["mention_seq"]),
                "channel_id": channel_id,
                "channel_name": channel_name_map.get(str(channel_id)) if channel_id else None,
                "post_id": row.get("post_id"),
                "mention_text": row["mention_text"],
                "context_snippet": row.get("context_snippet"),
                "mentioned_at": row["mentioned_at"],
            }
        )

    next_cursor = None
    if has_more and page_rows:
        next_cursor = _encode_mentions_cursor(int(page_rows[-1]["mention_seq"]))

    return {
        "items": items,
        "next_cursor": next_cursor,
        "has_more": has_more,
    }
