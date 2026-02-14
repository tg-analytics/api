import json
import re
from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import date, datetime, timedelta
from typing import Any

from supabase import Client

from app.schemas.mini_app import MiniAppSortBy, MiniAppsPeriod, SortOrder

_SEARCH_TERM_SANITIZE_RE = re.compile(r"[(),]")

_SORT_FIELD_MAP = {
    MiniAppSortBy.DAILY_USERS: "daily_users",
    MiniAppSortBy.GROWTH: "growth_weekly",
    MiniAppSortBy.RATING: "rating",
    MiniAppSortBy.LAUNCHED_AT: "launched_at",
}

_PERIOD_DAYS_MAP = {
    MiniAppsPeriod.D7: 7,
    MiniAppsPeriod.D30: 30,
}


def _encode_cursor(*, last_id: str, offset: int) -> str:
    payload = {"last_id": last_id, "offset": offset}
    raw = json.dumps(payload).encode("utf-8")
    return urlsafe_b64encode(raw).decode("utf-8")


def _decode_cursor(cursor: str) -> dict[str, Any]:
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


def _to_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def _apply_mini_app_filters(
    query: Any,
    *,
    q: str | None = None,
    category_slug: str | None = None,
    min_daily_users: int | None = None,
    min_rating: float | None = None,
    launch_within_days: int | None = None,
    min_growth: float | None = None,
) -> Any:
    if q:
        normalized_query = _SEARCH_TERM_SANITIZE_RE.sub(" ", q).strip()
        if normalized_query:
            query = query.or_(
                f"name.ilike.*{normalized_query}*,slug.ilike.*{normalized_query}*,description.ilike.*{normalized_query}*"
            )

    if category_slug:
        query = query.eq("category_slug", category_slug)

    if min_daily_users is not None:
        query = query.gte("daily_users", min_daily_users)

    if min_rating is not None:
        query = query.gte("rating", min_rating)

    if launch_within_days is not None:
        cutoff_date = date.today() - timedelta(days=launch_within_days)
        query = query.gte("launched_at", cutoff_date.isoformat())

    if min_growth is not None:
        query = query.gte("growth_weekly", min_growth)

    return query


def _normalize_mini_app_row(row: dict[str, Any]) -> dict[str, Any]:
    launched_at = _to_date(row.get("launched_at"))
    return {
        "mini_app_id": row["mini_app_id"],
        "name": row["name"],
        "slug": row["slug"],
        "category_slug": row.get("category_slug"),
        "daily_users": _to_int(row.get("daily_users")),
        "total_users": _to_int(row.get("total_users")),
        "sessions": _to_int(row.get("sessions")),
        "rating": _to_float(row.get("rating")),
        "growth_weekly": _to_float(row.get("growth_weekly")),
        "launched_at": launched_at.isoformat() if launched_at else None,
    }


def _aggregate_rows(rows: list[dict[str, Any]]) -> tuple[int, int, int]:
    daily_active_users = sum(_to_int(row.get("daily_users")) or 0 for row in rows)
    total_sessions = sum(_to_int(row.get("sessions")) or 0 for row in rows)

    avg_session_values = [
        value
        for value in (_to_int(row.get("avg_session_seconds")) for row in rows)
        if value is not None
    ]
    avg_session_seconds = (
        int(round(sum(avg_session_values) / len(avg_session_values))) if avg_session_values else 0
    )

    return daily_active_users, total_sessions, avg_session_seconds


def _delta_and_percent(
    *,
    value: int,
    baseline: int | None,
) -> tuple[int | None, float | None]:
    if baseline is None:
        return None, None

    delta = value - baseline
    if baseline == 0:
        return delta, None

    return delta, (delta / baseline) * 100


async def get_mini_apps_catalog(
    client: Client,
    *,
    q: str | None = None,
    category_slug: str | None = None,
    min_daily_users: int | None = None,
    min_rating: float | None = None,
    launch_within_days: int | None = None,
    min_growth: float | None = None,
    sort_by: MiniAppSortBy = MiniAppSortBy.DAILY_USERS,
    sort_order: SortOrder = SortOrder.DESC,
    limit: int = 20,
    cursor: str | None = None,
) -> dict[str, Any]:
    offset = 0
    if cursor:
        payload = _decode_cursor(cursor)
        offset = payload["offset"]

    base_query = client.table("vw_mini_apps_latest").select("*")
    base_query = _apply_mini_app_filters(
        base_query,
        q=q,
        category_slug=category_slug,
        min_daily_users=min_daily_users,
        min_rating=min_rating,
        launch_within_days=launch_within_days,
        min_growth=min_growth,
    )

    count_query = client.table("vw_mini_apps_latest").select(
        "mini_app_id",
        count="exact",
        head=True,
    )
    count_query = _apply_mini_app_filters(
        count_query,
        q=q,
        category_slug=category_slug,
        min_daily_users=min_daily_users,
        min_rating=min_rating,
        launch_within_days=launch_within_days,
        min_growth=min_growth,
    )
    total_response = count_query.execute()
    total_estimate = int(total_response.count or 0)

    sort_field = _SORT_FIELD_MAP[sort_by]
    is_desc = sort_order == SortOrder.DESC

    paged_query = (
        base_query.order(sort_field, desc=is_desc, nullsfirst=False)
        .order("mini_app_id", desc=is_desc)
        .range(offset, offset + limit)
    )

    response = paged_query.execute()
    rows = response.data or []
    has_more = len(rows) > limit
    page_rows = rows[:limit]

    next_cursor = None
    if has_more and page_rows:
        next_cursor = _encode_cursor(
            last_id=page_rows[-1]["mini_app_id"],
            offset=offset + limit,
        )

    return {
        "items": [_normalize_mini_app_row(row) for row in page_rows],
        "next_cursor": next_cursor,
        "has_more": has_more,
        "total_estimate": total_estimate,
    }


async def get_mini_apps_summary(client: Client, *, period: MiniAppsPeriod) -> dict[str, Any]:
    period_days = _PERIOD_DAYS_MAP[period]

    total_apps_response = client.table("mini_apps").select("id", count="exact", head=True).execute()
    total_mini_apps = int(total_apps_response.count or 0)

    latest_snapshot_response = (
        client.table("mini_app_metrics_daily")
        .select("metric_date")
        .order("metric_date", desc=True)
        .limit(1)
        .execute()
    )
    latest_snapshot_rows = latest_snapshot_response.data or []
    latest_snapshot_date = _to_date(latest_snapshot_rows[0]["metric_date"]) if latest_snapshot_rows else None

    if latest_snapshot_date is None:
        fallback_rows_response = (
            client.table("vw_mini_apps_latest")
            .select("daily_users, sessions, avg_session_seconds")
            .execute()
        )
        fallback_rows = fallback_rows_response.data or []
        daily_active_users, total_sessions, avg_session_seconds = _aggregate_rows(fallback_rows)
        return {
            "total_mini_apps": total_mini_apps,
            "daily_active_users": daily_active_users,
            "total_sessions": total_sessions,
            "avg_session_seconds": avg_session_seconds,
            "total_mini_apps_delta": 0,
            "daily_active_users_delta": None,
            "daily_active_users_delta_percent": None,
            "total_sessions_delta": None,
            "total_sessions_delta_percent": None,
            "avg_session_seconds_delta": None,
        }

    baseline_date = latest_snapshot_date - timedelta(days=period_days)

    current_rows_response = (
        client.table("mini_app_metrics_daily")
        .select("daily_users, sessions, avg_session_seconds")
        .eq("metric_date", latest_snapshot_date.isoformat())
        .execute()
    )
    current_rows = current_rows_response.data or []
    current_daily_active_users, current_total_sessions, current_avg_session_seconds = _aggregate_rows(current_rows)

    baseline_rows_response = (
        client.table("mini_app_metrics_daily")
        .select("daily_users, sessions, avg_session_seconds")
        .eq("metric_date", baseline_date.isoformat())
        .execute()
    )
    baseline_rows = baseline_rows_response.data or []

    baseline_daily_active_users: int | None = None
    baseline_total_sessions: int | None = None
    baseline_avg_session_seconds: int | None = None
    if baseline_rows:
        (
            baseline_daily_active_users,
            baseline_total_sessions,
            baseline_avg_session_seconds,
        ) = _aggregate_rows(baseline_rows)

    daily_active_users_delta, daily_active_users_delta_percent = _delta_and_percent(
        value=current_daily_active_users,
        baseline=baseline_daily_active_users,
    )
    total_sessions_delta, total_sessions_delta_percent = _delta_and_percent(
        value=current_total_sessions,
        baseline=baseline_total_sessions,
    )
    avg_session_seconds_delta = (
        current_avg_session_seconds - baseline_avg_session_seconds
        if baseline_avg_session_seconds is not None
        else None
    )

    launched_rows_response = client.table("mini_apps").select("launched_at").execute()
    launched_rows = launched_rows_response.data or []
    total_mini_apps_delta = 0
    for row in launched_rows:
        launched_at = _to_date(row.get("launched_at"))
        if launched_at and launched_at > baseline_date:
            total_mini_apps_delta += 1

    return {
        "total_mini_apps": total_mini_apps,
        "daily_active_users": current_daily_active_users,
        "total_sessions": current_total_sessions,
        "avg_session_seconds": current_avg_session_seconds,
        "total_mini_apps_delta": total_mini_apps_delta,
        "daily_active_users_delta": daily_active_users_delta,
        "daily_active_users_delta_percent": daily_active_users_delta_percent,
        "total_sessions_delta": total_sessions_delta,
        "total_sessions_delta_percent": total_sessions_delta_percent,
        "avg_session_seconds_delta": avg_session_seconds_delta,
    }
