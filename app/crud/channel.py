import json
import re
from base64 import urlsafe_b64decode, urlsafe_b64encode
from typing import Any

from supabase import Client

from app.schemas.channel import ChannelSizeBucket, ChannelSortBy, ChannelStatus, SortOrder

_SEARCH_TERM_SANITIZE_RE = re.compile(r"[(),]")


def _encode_cursor(*, last_id: str, offset: int) -> str:
    """Encode pagination cursor payload for channels listing."""
    payload = {"last_id": last_id, "offset": offset}
    raw = json.dumps(payload).encode("utf-8")
    return urlsafe_b64encode(raw).decode("utf-8")


def _decode_cursor(cursor: str) -> dict[str, Any]:
    """Decode a channels pagination cursor.

    Raises:
        ValueError: If cursor is invalid or missing required fields.
    """
    try:
        raw = urlsafe_b64decode(cursor).decode("utf-8")
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

    payload["offset"] = offset
    return payload


def _apply_channel_filters(
    query: Any,
    *,
    q: str | None = None,
    country_code: str | None = None,
    category_slug: str | None = None,
    size_bucket: ChannelSizeBucket | None = None,
    er_min: float | None = None,
    er_max: float | None = None,
    status: ChannelStatus | None = None,
    verified: bool | None = None,
    scam: bool | None = None,
) -> Any:
    """Apply channel list filters to a Supabase query object."""
    if q:
        normalized_query = _SEARCH_TERM_SANITIZE_RE.sub(" ", q).strip()
        if normalized_query:
            query = query.or_(
                f"name.ilike.*{normalized_query}*,username.ilike.*{normalized_query}*"
            )

    if country_code:
        query = query.eq("country_code", country_code.upper())

    if category_slug:
        query = query.eq("category_slug", category_slug)

    if size_bucket:
        query = query.eq("size_bucket", size_bucket.value)

    if er_min is not None:
        query = query.gte("engagement_rate", er_min)

    if er_max is not None:
        query = query.lte("engagement_rate", er_max)

    if status:
        query = query.eq("status", status.value)

    if verified is not None:
        query = query.eq("verified", verified)

    if scam is not None:
        query = query.eq("scam", scam)

    return query


def _normalize_channel_row(row: dict[str, Any]) -> dict[str, Any]:
    """Normalize channel row fields for API response."""
    username = row.get("username")
    if username and not str(username).startswith("@"):
        username = f"@{username}"

    return {
        "channel_id": row["channel_id"],
        "name": row["name"],
        "username": username,
        "subscribers": int(row["subscribers"] or 0),
        "growth_24h": row.get("growth_24h"),
        "growth_7d": row.get("growth_7d"),
        "growth_30d": row.get("growth_30d"),
        "engagement_rate": row.get("engagement_rate"),
        "category_slug": row.get("category_slug"),
        "category_name": row.get("category_name"),
        "country_code": row.get("country_code"),
        "status": row["status"],
        "verified": bool(row.get("verified")),
        "scam": bool(row.get("scam")),
    }


async def get_catalog_channels(
    client: Client,
    *,
    q: str | None = None,
    country_code: str | None = None,
    category_slug: str | None = None,
    size_bucket: ChannelSizeBucket | None = None,
    er_min: float | None = None,
    er_max: float | None = None,
    status: ChannelStatus | None = None,
    verified: bool | None = None,
    scam: bool | None = None,
    sort_by: ChannelSortBy = ChannelSortBy.SUBSCRIBERS,
    sort_order: SortOrder = SortOrder.DESC,
    limit: int = 20,
    cursor: str | None = None,
) -> dict[str, Any]:
    """List channels from catalog view with filtering, sorting, and pagination."""
    offset = 0
    if cursor:
        payload = _decode_cursor(cursor)
        offset = payload["offset"]

    base_query = client.table("vw_catalog_channels").select("*")
    base_query = _apply_channel_filters(
        base_query,
        q=q,
        country_code=country_code,
        category_slug=category_slug,
        size_bucket=size_bucket,
        er_min=er_min,
        er_max=er_max,
        status=status,
        verified=verified,
        scam=scam,
    )

    count_query = client.table("vw_catalog_channels").select(
        "channel_id",
        count="exact",
        head=True,
    )
    count_query = _apply_channel_filters(
        count_query,
        q=q,
        country_code=country_code,
        category_slug=category_slug,
        size_bucket=size_bucket,
        er_min=er_min,
        er_max=er_max,
        status=status,
        verified=verified,
        scam=scam,
    )
    total_response = count_query.execute()
    total_estimate = int(total_response.count or 0)

    is_desc = sort_order == SortOrder.DESC
    paged_query = (
        base_query.order(sort_by.value, desc=is_desc, nullsfirst=False)
        .order("channel_id", desc=is_desc)
        .range(offset, offset + limit)
    )

    response = paged_query.execute()
    rows = response.data or []
    has_more = len(rows) > limit
    page_rows = rows[:limit]

    next_cursor = None
    if has_more and page_rows:
        next_cursor = _encode_cursor(
            last_id=page_rows[-1]["channel_id"],
            offset=offset + limit,
        )

    items = [_normalize_channel_row(row) for row in page_rows]
    return {
        "items": items,
        "next_cursor": next_cursor,
        "has_more": has_more,
        "total_estimate": total_estimate,
    }
