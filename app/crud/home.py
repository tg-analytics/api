import json
from base64 import urlsafe_b64decode, urlsafe_b64encode
from typing import Any

from supabase import Client


def _encode_cursor(*, offset: int) -> str:
    payload = {"offset": offset}
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return urlsafe_b64encode(raw).decode("utf-8")


def _decode_cursor(cursor: str) -> int:
    try:
        padding = "=" * (-len(cursor) % 4)
        raw = urlsafe_b64decode(f"{cursor}{padding}").decode("utf-8")
        payload = json.loads(raw)
    except Exception as exc:  # noqa: BLE001 - cursor decoding must be robust
        raise ValueError("Invalid pagination cursor") from exc

    if not isinstance(payload, dict) or "offset" not in payload:
        raise ValueError("Invalid pagination cursor")

    try:
        offset = int(payload["offset"])
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid pagination cursor") from exc

    if offset < 0:
        raise ValueError("Invalid pagination cursor")

    return offset


def _normalize_category_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "slug": row["slug"],
        "name": row["name"],
        "icon": row.get("icon"),
        "channels_count": int(row.get("channels_count") or 0),
    }


async def get_home_categories(
    client: Client,
    *,
    limit: int = 20,
    cursor: str | None = None,
) -> dict[str, Any]:
    offset = 0
    if cursor:
        offset = _decode_cursor(cursor)

    response = (
        client.table("categories")
        .select("slug, name, icon, channels_count")
        .order("name", desc=False)
        .range(offset, offset + limit)
        .execute()
    )
    rows = response.data or []

    has_more = len(rows) > limit
    page_rows = rows[:limit]
    next_cursor = _encode_cursor(offset=offset + limit) if has_more else None

    total_response = client.table("categories").select("id", count="exact", head=True).execute()
    total_estimate = int(total_response.count or 0)

    return {
        "items": [_normalize_category_row(row) for row in page_rows],
        "next_cursor": next_cursor,
        "has_more": has_more,
        "total_estimate": total_estimate,
    }
