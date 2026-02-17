import json
import re
from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import date, datetime, timedelta, timezone
from typing import Any

from supabase import Client

from app.schemas.advertiser import AdvertiserActivityStatus, AdvertiserSortBy, SortOrder

_SEARCH_TERM_SANITIZE_RE = re.compile(r"[(),]")

_SORT_FIELD_MAP = {
    AdvertiserSortBy.ESTIMATED_SPEND: "estimated_spend",
    AdvertiserSortBy.TOTAL_ADS: "total_ads",
    AdvertiserSortBy.CHANNELS_USED: "channels_used",
    AdvertiserSortBy.AVG_ENGAGEMENT_RATE: "avg_engagement_rate",
    AdvertiserSortBy.TREND: "trend",
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


def _to_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)

    value_str = str(value).strip()
    if not value_str:
        return None
    if value_str.endswith("Z"):
        value_str = value_str[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(value_str)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _normalize_username(username: Any) -> str | None:
    if username is None:
        return None
    username_str = str(username)
    if username_str.startswith("@"):
        return username_str
    return f"@{username_str}"


def _delta_and_percent(
    *,
    value: int | float,
    baseline: int | float | None,
) -> tuple[int | float | None, float | None]:
    if baseline is None:
        return None, None

    delta = value - baseline
    if baseline == 0:
        return delta, None
    return delta, (delta / baseline) * 100


def _sort_records(
    records: list[dict[str, Any]],
    *,
    sort_field: str,
    sort_order: SortOrder,
) -> list[dict[str, Any]]:
    non_null_rows = [row for row in records if row.get(sort_field) is not None]
    null_rows = [row for row in records if row.get(sort_field) is None]

    is_desc = sort_order == SortOrder.DESC
    non_null_rows.sort(
        key=lambda row: (row.get(sort_field), row["advertiser_id"]),
        reverse=is_desc,
    )
    return non_null_rows + null_rows


def _matches_activity_status(
    *,
    last_active_at: str | None,
    activity_status: AdvertiserActivityStatus,
) -> bool:
    if activity_status == AdvertiserActivityStatus.ALL:
        return True

    last_active_dt = _to_datetime(last_active_at)
    if last_active_dt is None:
        return False

    now = datetime.now(timezone.utc)
    days = 7 if activity_status == AdvertiserActivityStatus.ACTIVE else 30
    return last_active_dt >= (now - timedelta(days=days))


def _compute_trend(
    *,
    current_spend: float | None,
    baseline_spend: float | None,
    fallback_trend: float | None,
) -> float | None:
    if current_spend is None or baseline_spend is None:
        return fallback_trend
    if baseline_spend == 0:
        return None
    return ((current_spend - baseline_spend) / baseline_spend) * 100


def _get_latest_snapshot_date(client: Client) -> date | None:
    response = (
        client.table("advertiser_metrics_daily")
        .select("metric_date")
        .order("metric_date", desc=True)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    return _to_date(rows[0]["metric_date"]) if rows else None


def _get_industries_map(client: Client) -> dict[str, dict[str, str]]:
    response = client.table("industries").select("id, slug, name").execute()
    rows = response.data or []

    industries: dict[str, dict[str, str]] = {}
    for row in rows:
        industry_id = row.get("id")
        if industry_id is None:
            continue
        industries[str(industry_id)] = {
            "slug": str(row.get("slug")) if row.get("slug") is not None else "",
            "name": str(row.get("name")) if row.get("name") is not None else "",
        }
    return industries


def _get_metrics_map(client: Client, metric_date: date) -> dict[str, dict[str, Any]]:
    response = (
        client.table("advertiser_metrics_daily")
        .select(
            "advertiser_id, estimated_spend, total_ads, active_creatives, channels_used, avg_engagement_rate, trend_percent"
        )
        .eq("metric_date", metric_date.isoformat())
        .execute()
    )
    rows = response.data or []
    return {str(row["advertiser_id"]): row for row in rows if row.get("advertiser_id") is not None}


def _get_last_activity_map(client: Client) -> dict[str, str]:
    response = client.table("ad_creatives").select("advertiser_id, posted_at, last_seen_at").execute()
    rows = response.data or []

    last_activity: dict[str, datetime] = {}
    for row in rows:
        advertiser_id = row.get("advertiser_id")
        if advertiser_id is None:
            continue

        advertiser_id_str = str(advertiser_id)
        posted_at = _to_datetime(row.get("posted_at"))
        last_seen_at = _to_datetime(row.get("last_seen_at"))

        candidate = last_seen_at or posted_at
        if posted_at and last_seen_at:
            candidate = max(posted_at, last_seen_at)

        if candidate is None:
            continue

        prev = last_activity.get(advertiser_id_str)
        if prev is None or candidate > prev:
            last_activity[advertiser_id_str] = candidate

    return {
        advertiser_id: activity_dt.isoformat().replace("+00:00", "Z")
        for advertiser_id, activity_dt in last_activity.items()
    }


def _build_advertiser_records(
    client: Client,
    *,
    time_period_days: int,
) -> tuple[list[dict[str, Any]], date | None, date | None]:
    advertisers_response = (
        client.table("advertisers")
        .select(
            "id, name, slug, industry_id, logo_url, website_url, description, active_creatives_count, estimated_spend_current, avg_engagement_rate_current, total_ads_current, channels_used_current, trend_30d"
        )
        .execute()
    )
    advertisers_rows = advertisers_response.data or []

    snapshot_date = _get_latest_snapshot_date(client)
    baseline_date = snapshot_date - timedelta(days=time_period_days) if snapshot_date else None

    metrics_map: dict[str, dict[str, Any]] = {}
    baseline_map: dict[str, dict[str, Any]] = {}
    if snapshot_date:
        metrics_map = _get_metrics_map(client, snapshot_date)
    if baseline_date:
        baseline_map = _get_metrics_map(client, baseline_date)

    industries_map = _get_industries_map(client)
    last_activity_map = _get_last_activity_map(client)

    records: list[dict[str, Any]] = []
    for advertiser_row in advertisers_rows:
        advertiser_id = str(advertiser_row["id"])
        metric_row = metrics_map.get(advertiser_id, {})
        baseline_row = baseline_map.get(advertiser_id, {})

        industry_id = advertiser_row.get("industry_id")
        industry = industries_map.get(str(industry_id), {}) if industry_id else {}

        estimated_spend = _to_float(metric_row.get("estimated_spend"))
        total_ads = _to_int(metric_row.get("total_ads"))
        active_creatives = _to_int(metric_row.get("active_creatives"))
        channels_used = _to_int(metric_row.get("channels_used"))
        avg_engagement_rate = _to_float(metric_row.get("avg_engagement_rate"))

        if estimated_spend is None:
            estimated_spend = _to_float(advertiser_row.get("estimated_spend_current"))
        if total_ads is None:
            total_ads = _to_int(advertiser_row.get("total_ads_current"))
        if active_creatives is None:
            active_creatives = _to_int(advertiser_row.get("active_creatives_count"))
        if channels_used is None:
            channels_used = _to_int(advertiser_row.get("channels_used_current"))
        if avg_engagement_rate is None:
            avg_engagement_rate = _to_float(advertiser_row.get("avg_engagement_rate_current"))

        baseline_estimated_spend = _to_float(baseline_row.get("estimated_spend"))
        baseline_total_ads = _to_int(baseline_row.get("total_ads"))
        baseline_active_creatives = _to_int(baseline_row.get("active_creatives"))
        baseline_avg_engagement_rate = _to_float(baseline_row.get("avg_engagement_rate"))

        fallback_trend = _to_float(metric_row.get("trend_percent"))
        if fallback_trend is None:
            fallback_trend = _to_float(advertiser_row.get("trend_30d"))

        trend = _compute_trend(
            current_spend=estimated_spend,
            baseline_spend=baseline_estimated_spend,
            fallback_trend=fallback_trend,
        )

        records.append(
            {
                "advertiser_id": advertiser_id,
                "name": advertiser_row["name"],
                "slug": advertiser_row["slug"],
                "logo_url": advertiser_row.get("logo_url"),
                "industry_slug": industry.get("slug") or None,
                "industry_name": industry.get("name") or None,
                "estimated_spend": estimated_spend,
                "total_ads": total_ads,
                "channels_used": channels_used,
                "avg_engagement_rate": avg_engagement_rate,
                "trend": trend,
                "active_creatives": active_creatives,
                "last_active_at": last_activity_map.get(advertiser_id),
                "website_url": advertiser_row.get("website_url"),
                "description": advertiser_row.get("description"),
                "baseline_estimated_spend": baseline_estimated_spend,
                "baseline_total_ads": baseline_total_ads,
                "baseline_active_creatives": baseline_active_creatives,
                "baseline_avg_engagement_rate": baseline_avg_engagement_rate,
            }
        )

    return records, snapshot_date, baseline_date


async def get_advertisers_catalog(
    client: Client,
    *,
    q: str | None = None,
    industry_slug: str | None = None,
    time_period_days: int = 30,
    min_spend: float | None = None,
    min_channels: int | None = None,
    min_engagement: float | None = None,
    activity_status: AdvertiserActivityStatus = AdvertiserActivityStatus.ALL,
    sort_by: AdvertiserSortBy = AdvertiserSortBy.ESTIMATED_SPEND,
    sort_order: SortOrder = SortOrder.DESC,
    limit: int = 20,
    cursor: str | None = None,
) -> dict[str, Any]:
    offset = 0
    if cursor:
        payload = _decode_cursor(cursor)
        offset = payload["offset"]

    records, snapshot_date, baseline_date = _build_advertiser_records(
        client,
        time_period_days=time_period_days,
    )

    normalized_q: str | None = None
    if q:
        normalized_q = _SEARCH_TERM_SANITIZE_RE.sub(" ", q).strip().lower()

    normalized_industry_slug = industry_slug.lower() if industry_slug else None

    filtered: list[dict[str, Any]] = []
    for record in records:
        if normalized_q:
            if (
                normalized_q not in str(record.get("name", "")).lower()
                and normalized_q not in str(record.get("slug", "")).lower()
                and normalized_q not in str(record.get("description", "")).lower()
            ):
                continue

        if normalized_industry_slug and (record.get("industry_slug") or "").lower() != normalized_industry_slug:
            continue

        if min_spend is not None and (
            record.get("estimated_spend") is None or record["estimated_spend"] < min_spend
        ):
            continue

        if min_channels is not None and (
            record.get("channels_used") is None or record["channels_used"] < min_channels
        ):
            continue

        if min_engagement is not None and (
            record.get("avg_engagement_rate") is None or record["avg_engagement_rate"] < min_engagement
        ):
            continue

        if not _matches_activity_status(
            last_active_at=record.get("last_active_at"),
            activity_status=activity_status,
        ):
            continue

        filtered.append(record)

    total_estimate = len(filtered)
    sort_field = _SORT_FIELD_MAP[sort_by]
    sorted_records = _sort_records(
        filtered,
        sort_field=sort_field,
        sort_order=sort_order,
    )

    page_rows = sorted_records[offset : offset + limit]
    has_more = (offset + limit) < len(sorted_records)
    next_cursor = None
    if has_more and page_rows:
        next_cursor = _encode_cursor(
            last_id=page_rows[-1]["advertiser_id"],
            offset=offset + limit,
        )

    items: list[dict[str, Any]] = []
    for index, row in enumerate(page_rows):
        items.append(
            {
                "rank": offset + index + 1,
                "advertiser_id": row["advertiser_id"],
                "name": row["name"],
                "slug": row["slug"],
                "logo_url": row.get("logo_url"),
                "industry_slug": row.get("industry_slug"),
                "industry_name": row.get("industry_name"),
                "estimated_spend": row.get("estimated_spend"),
                "total_ads": row.get("total_ads"),
                "channels_used": row.get("channels_used"),
                "avg_engagement_rate": row.get("avg_engagement_rate"),
                "trend": row.get("trend"),
                "active_creatives": row.get("active_creatives"),
                "last_active_at": row.get("last_active_at"),
            }
        )

    return {
        "items": items,
        "next_cursor": next_cursor,
        "has_more": has_more,
        "total_estimate": total_estimate,
        "snapshot_date": snapshot_date.isoformat() if snapshot_date else None,
        "baseline_date": baseline_date.isoformat() if baseline_date else None,
    }


async def get_advertisers_summary(
    client: Client,
    *,
    time_period_days: int = 30,
) -> dict[str, Any]:
    records, snapshot_date, baseline_date = _build_advertiser_records(
        client,
        time_period_days=time_period_days,
    )

    active_advertisers = sum(1 for row in records if (row.get("active_creatives") or 0) > 0)
    total_ad_spend = float(sum(row.get("estimated_spend") or 0 for row in records))
    ad_campaigns = int(sum(row.get("total_ads") or 0 for row in records))

    avg_engagement_values = [row["avg_engagement_rate"] for row in records if row.get("avg_engagement_rate") is not None]
    avg_engagement_rate = float(sum(avg_engagement_values) / len(avg_engagement_values)) if avg_engagement_values else 0.0

    has_baseline = baseline_date is not None and any(
        row.get("baseline_estimated_spend") is not None for row in records
    )

    active_advertisers_delta: int | None = None
    total_ad_spend_delta: float | None = None
    total_ad_spend_delta_percent: float | None = None
    ad_campaigns_delta: int | None = None
    ad_campaigns_delta_percent: float | None = None
    avg_engagement_rate_delta: float | None = None
    avg_engagement_rate_delta_percent: float | None = None

    if has_baseline:
        baseline_active_advertisers = sum(
            1 for row in records if (row.get("baseline_active_creatives") or 0) > 0
        )
        baseline_total_ad_spend = float(sum(row.get("baseline_estimated_spend") or 0 for row in records))
        baseline_ad_campaigns = int(sum(row.get("baseline_total_ads") or 0 for row in records))

        baseline_avg_engagement_values = [
            row["baseline_avg_engagement_rate"]
            for row in records
            if row.get("baseline_avg_engagement_rate") is not None
        ]
        baseline_avg_engagement_rate = (
            float(sum(baseline_avg_engagement_values) / len(baseline_avg_engagement_values))
            if baseline_avg_engagement_values
            else None
        )

        active_delta, _ = _delta_and_percent(
            value=active_advertisers,
            baseline=baseline_active_advertisers,
        )
        spend_delta, spend_delta_percent = _delta_and_percent(
            value=total_ad_spend,
            baseline=baseline_total_ad_spend,
        )
        campaigns_delta, campaigns_delta_percent = _delta_and_percent(
            value=ad_campaigns,
            baseline=baseline_ad_campaigns,
        )
        avg_er_delta, avg_er_delta_percent = _delta_and_percent(
            value=avg_engagement_rate,
            baseline=baseline_avg_engagement_rate,
        )

        active_advertisers_delta = _to_int(active_delta)
        total_ad_spend_delta = _to_float(spend_delta)
        total_ad_spend_delta_percent = _to_float(spend_delta_percent)
        ad_campaigns_delta = _to_int(campaigns_delta)
        ad_campaigns_delta_percent = _to_float(campaigns_delta_percent)
        avg_engagement_rate_delta = _to_float(avg_er_delta)
        avg_engagement_rate_delta_percent = _to_float(avg_er_delta_percent)

    return {
        "active_advertisers": active_advertisers,
        "total_ad_spend": total_ad_spend,
        "ad_campaigns": ad_campaigns,
        "avg_engagement_rate": avg_engagement_rate,
        "active_advertisers_delta": active_advertisers_delta,
        "total_ad_spend_delta": total_ad_spend_delta,
        "total_ad_spend_delta_percent": total_ad_spend_delta_percent,
        "ad_campaigns_delta": ad_campaigns_delta,
        "ad_campaigns_delta_percent": ad_campaigns_delta_percent,
        "avg_engagement_rate_delta": avg_engagement_rate_delta,
        "avg_engagement_rate_delta_percent": avg_engagement_rate_delta_percent,
        "snapshot_date": snapshot_date.isoformat() if snapshot_date else None,
        "baseline_date": baseline_date.isoformat() if baseline_date else None,
    }


def _get_latest_top_channels_snapshot_date(client: Client, advertiser_id: str) -> date | None:
    response = (
        client.table("advertiser_top_channels_daily")
        .select("snapshot_date")
        .eq("advertiser_id", advertiser_id)
        .order("snapshot_date", desc=True)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    return _to_date(rows[0]["snapshot_date"]) if rows else None


def _get_top_channels(
    client: Client,
    *,
    advertiser_id: str,
    snapshot_date: date,
    limit: int = 10,
) -> list[dict[str, Any]]:
    top_channels_response = (
        client.table("advertiser_top_channels_daily")
        .select("channel_id, rank, impressions, estimated_spend, engagement_rate")
        .eq("advertiser_id", advertiser_id)
        .eq("snapshot_date", snapshot_date.isoformat())
        .order("rank", desc=False)
        .limit(limit)
        .execute()
    )
    top_channel_rows = top_channels_response.data or []

    channel_ids = [str(row["channel_id"]) for row in top_channel_rows if row.get("channel_id")]
    channel_map: dict[str, dict[str, Any]] = {}
    if channel_ids:
        channels_response = (
            client.table("channels")
            .select("id, name, username")
            .in_("id", channel_ids)
            .execute()
        )
        channel_map = {
            str(row["id"]): row for row in (channels_response.data or []) if row.get("id") is not None
        }

    items: list[dict[str, Any]] = []
    for row in top_channel_rows:
        channel_id = str(row["channel_id"])
        channel = channel_map.get(channel_id, {})
        items.append(
            {
                "channel_id": channel_id,
                "name": channel.get("name") or "Unknown Channel",
                "username": _normalize_username(channel.get("username")),
                "rank": _to_int(row.get("rank")) or 0,
                "impressions": _to_int(row.get("impressions")),
                "estimated_spend": _to_float(row.get("estimated_spend")),
                "engagement_rate": _to_float(row.get("engagement_rate")),
            }
        )
    return items


async def get_advertiser_detail(
    client: Client,
    *,
    advertiser_id: str,
    time_period_days: int = 30,
) -> dict[str, Any] | None:
    records, snapshot_date, baseline_date = _build_advertiser_records(
        client,
        time_period_days=time_period_days,
    )

    advertiser_row = next((row for row in records if row["advertiser_id"] == advertiser_id), None)
    if advertiser_row is None:
        return None

    channels_snapshot_date = _get_latest_top_channels_snapshot_date(client, advertiser_id)
    top_channels = []
    if channels_snapshot_date:
        top_channels = _get_top_channels(
            client,
            advertiser_id=advertiser_id,
            snapshot_date=channels_snapshot_date,
        )

    # Keep detail trend consistent with listing semantics.
    trend = _compute_trend(
        current_spend=advertiser_row.get("estimated_spend"),
        baseline_spend=advertiser_row.get("baseline_estimated_spend") if baseline_date else None,
        fallback_trend=advertiser_row.get("trend"),
    )

    return {
        "advertiser_id": advertiser_row["advertiser_id"],
        "name": advertiser_row["name"],
        "slug": advertiser_row["slug"],
        "logo_url": advertiser_row.get("logo_url"),
        "industry_slug": advertiser_row.get("industry_slug"),
        "industry_name": advertiser_row.get("industry_name"),
        "estimated_spend": advertiser_row.get("estimated_spend"),
        "total_ads": advertiser_row.get("total_ads"),
        "channels_used": advertiser_row.get("channels_used"),
        "avg_engagement_rate": advertiser_row.get("avg_engagement_rate"),
        "trend": trend,
        "active_creatives": advertiser_row.get("active_creatives"),
        "last_active_at": advertiser_row.get("last_active_at"),
        "website_url": advertiser_row.get("website_url"),
        "description": advertiser_row.get("description"),
        "top_channels": top_channels,
        "snapshot_date": snapshot_date.isoformat() if snapshot_date else None,
    }
