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
    return {
        "channel_id": row["channel_id"],
        "name": row["name"],
        "username": _normalize_username(row.get("username")),
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


def _normalize_username(username: Any) -> str | None:
    if username is None:
        return None

    username_str = str(username)
    if username_str.startswith("@"):
        return username_str
    return f"@{username_str}"


def _to_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _compute_kpi(value: int | float | None, baseline: int | float | None) -> dict[str, Any]:
    if value is None:
        return {"value": None, "delta": None, "delta_percent": None}

    delta: int | float | None = None
    delta_percent: float | None = None

    if baseline is not None:
        delta = value - baseline
        if baseline != 0:
            delta_percent = (delta / baseline) * 100

    return {
        "value": value,
        "delta": delta,
        "delta_percent": delta_percent,
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


async def get_channel_overview(client: Client, channel_id: str) -> dict[str, Any] | None:
    overview_response = (
        client.table("vw_channel_overview")
        .select("*")
        .eq("channel_id", channel_id)
        .limit(1)
        .execute()
    )
    overview_rows = overview_response.data or []
    if not overview_rows:
        return None

    overview_row = overview_rows[0]

    metrics_response = (
        client.table("channel_metrics_daily")
        .select("metric_date, subscribers, avg_views, engagement_rate, posts_per_day")
        .eq("channel_id", channel_id)
        .order("metric_date", desc=True)
        .limit(30)
        .execute()
    )
    metrics_rows_desc = metrics_response.data or []
    baseline_row = metrics_rows_desc[-1] if metrics_rows_desc else None

    current_subscribers = _to_int(overview_row.get("subscribers"))
    current_avg_views = _to_int(overview_row.get("avg_views"))
    current_engagement_rate = _to_float(overview_row.get("engagement_rate"))
    current_posts_per_day = _to_float(overview_row.get("posts_per_day"))

    baseline_subscribers = _to_int(baseline_row.get("subscribers")) if baseline_row else None
    baseline_avg_views = _to_int(baseline_row.get("avg_views")) if baseline_row else None
    baseline_engagement_rate = _to_float(baseline_row.get("engagement_rate")) if baseline_row else None
    baseline_posts_per_day = _to_float(baseline_row.get("posts_per_day")) if baseline_row else None

    chart_points: list[dict[str, Any]] = []
    for metric_row in reversed(metrics_rows_desc):
        metric_date = metric_row.get("metric_date")
        if metric_date is None:
            continue

        chart_points.append(
            {
                "date": str(metric_date),
                "subscribers": _to_int(metric_row.get("subscribers")),
                "engagement_rate": _to_float(metric_row.get("engagement_rate")),
            }
        )

    similarities_response = (
        client.table("channel_similarities")
        .select("similar_channel_id, similarity_score")
        .eq("channel_id", channel_id)
        .order("similarity_score", desc=True)
        .limit(5)
        .execute()
    )
    similarity_rows = similarities_response.data or []

    similar_channels: list[dict[str, Any]] = []
    for similarity_row in similarity_rows:
        similar_channel_id = similarity_row.get("similar_channel_id")
        if similar_channel_id is None:
            continue

        similar_channel_response = (
            client.table("channels")
            .select("id, name, username, subscribers_current")
            .eq("id", similar_channel_id)
            .limit(1)
            .execute()
        )
        similar_channel_rows = similar_channel_response.data or []
        if not similar_channel_rows:
            continue

        similar_channel_row = similar_channel_rows[0]
        similar_channels.append(
            {
                "channel_id": similar_channel_row["id"],
                "name": similar_channel_row["name"],
                "username": _normalize_username(similar_channel_row.get("username")),
                "subscribers": _to_int(similar_channel_row.get("subscribers_current")),
                "similarity_score": _to_float(similarity_row.get("similarity_score")) or 0.0,
            }
        )

    tags_response = (
        client.table("channel_tags")
        .select("tag_id, relevance_score")
        .eq("channel_id", channel_id)
        .order("relevance_score", desc=True)
        .limit(10)
        .execute()
    )
    channel_tag_rows = tags_response.data or []

    tags: list[dict[str, Any]] = []
    for channel_tag_row in channel_tag_rows:
        tag_id = channel_tag_row.get("tag_id")
        if tag_id is None:
            continue

        tag_response = client.table("tags").select("id, slug, name").eq("id", tag_id).limit(1).execute()
        tag_rows = tag_response.data or []
        if not tag_rows:
            continue

        tag_row = tag_rows[0]
        tags.append(
            {
                "tag_id": tag_row["id"],
                "slug": tag_row["slug"],
                "name": tag_row["name"],
                "relevance_score": _to_float(channel_tag_row.get("relevance_score")),
            }
        )

    posts_response = (
        client.table("posts")
        .select(
            "id, telegram_message_id, published_at, title, content_text, views_count, "
            "reactions_count, comments_count, forwards_count, external_post_url"
        )
        .eq("channel_id", channel_id)
        .eq("is_deleted", False)
        .order("published_at", desc=True)
        .limit(5)
        .execute()
    )
    recent_post_rows = posts_response.data or []

    recent_posts = [
        {
            "post_id": post_row["id"],
            "telegram_message_id": int(post_row["telegram_message_id"]),
            "published_at": str(post_row["published_at"]),
            "title": post_row.get("title"),
            "content_text": post_row.get("content_text"),
            "views_count": _to_int(post_row.get("views_count")) or 0,
            "reactions_count": _to_int(post_row.get("reactions_count")) or 0,
            "comments_count": _to_int(post_row.get("comments_count")) or 0,
            "forwards_count": _to_int(post_row.get("forwards_count")) or 0,
            "external_post_url": post_row.get("external_post_url"),
        }
        for post_row in recent_post_rows
    ]

    incoming_30d = _to_int(overview_row.get("incoming_30d")) or 0
    outgoing_30d = _to_int(overview_row.get("outgoing_30d")) or 0

    return {
        "channel": {
            "channel_id": overview_row["channel_id"],
            "telegram_channel_id": int(overview_row["telegram_channel_id"]),
            "name": overview_row["name"],
            "username": _normalize_username(overview_row.get("username")),
            "avatar_url": overview_row.get("avatar_url"),
            "description": overview_row.get("description"),
            "about_text": overview_row.get("about_text"),
            "website_url": overview_row.get("website_url"),
            "status": overview_row["status"],
            "country_code": overview_row.get("country_code"),
            "category_slug": overview_row.get("category_slug"),
            "category_name": overview_row.get("category_name"),
        },
        "kpis": {
            "subscribers": _compute_kpi(current_subscribers, baseline_subscribers),
            "avg_views": _compute_kpi(current_avg_views, baseline_avg_views),
            "engagement_rate": _compute_kpi(current_engagement_rate, baseline_engagement_rate),
            "posts_per_day": _compute_kpi(current_posts_per_day, baseline_posts_per_day),
        },
        "chart": {
            "range": "30d",
            "points": chart_points,
        },
        "similar_channels": similar_channels,
        "tags": tags,
        "recent_posts": recent_posts,
        "inout_30d": {
            "incoming": incoming_30d,
            "outgoing": outgoing_30d,
        },
        "incoming_30d": incoming_30d,
        "outgoing_30d": outgoing_30d,
    }
