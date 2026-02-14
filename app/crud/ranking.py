from __future__ import annotations

from typing import Any

from supabase import Client


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


def _get_channels_map(client: Client, channel_ids: list[str]) -> dict[str, dict[str, Any]]:
    if not channel_ids:
        return {}

    response = (
        client.table("channels")
        .select("id, name, username")
        .in_("id", channel_ids)
        .execute()
    )
    rows = response.data or []
    return {str(row["id"]): row for row in rows if row.get("id") is not None}


def _get_country_name(client: Client, country_code: str) -> str | None:
    response = (
        client.table("countries")
        .select("name")
        .eq("code", country_code)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    return rows[0].get("name") if rows else None


async def get_country_rankings(
    client: Client,
    *,
    country_code: str,
    limit: int,
) -> dict[str, Any]:
    normalized_country_code = country_code.upper()

    latest_snapshot_response = (
        client.table("channel_rankings_daily")
        .select("snapshot_date")
        .eq("ranking_scope", "country")
        .eq("country_code", normalized_country_code)
        .order("snapshot_date", desc=True)
        .limit(1)
        .execute()
    )
    latest_snapshot_rows = latest_snapshot_response.data or []
    snapshot_date = (
        str(latest_snapshot_rows[0]["snapshot_date"]) if latest_snapshot_rows else None
    )

    country_name = _get_country_name(client, normalized_country_code)
    if snapshot_date is None:
        return {
            "items": [],
            "meta": {
                "country_code": normalized_country_code,
                "country_name": country_name,
                "snapshot_date": None,
                "total_ranked_channels": 0,
                "applied_limit": limit,
            },
        }

    count_response = (
        client.table("channel_rankings_daily")
        .select("id", count="exact", head=True)
        .eq("ranking_scope", "country")
        .eq("country_code", normalized_country_code)
        .eq("snapshot_date", snapshot_date)
        .execute()
    )
    total_ranked_channels = int(count_response.count or 0)

    rankings_response = (
        client.table("channel_rankings_daily")
        .select("channel_id, rank, subscribers, growth_7d, engagement_rate")
        .eq("ranking_scope", "country")
        .eq("country_code", normalized_country_code)
        .eq("snapshot_date", snapshot_date)
        .order("rank", desc=False)
        .limit(limit)
        .execute()
    )
    ranking_rows = rankings_response.data or []
    channel_ids = [str(row["channel_id"]) for row in ranking_rows if row.get("channel_id")]
    channels_map = _get_channels_map(client, channel_ids)

    context_label = country_name or normalized_country_code
    items: list[dict[str, Any]] = []
    for row in ranking_rows:
        channel_id = str(row["channel_id"])
        channel_row = channels_map.get(channel_id, {})
        items.append(
            {
                "rank": _to_int(row.get("rank")) or 0,
                "channel_id": channel_id,
                "name": channel_row.get("name") or "Unknown Channel",
                "username": _normalize_username(channel_row.get("username")),
                "subscribers": _to_int(row.get("subscribers")),
                "growth_7d": _to_float(row.get("growth_7d")),
                "engagement_rate": _to_float(row.get("engagement_rate")),
                "context_type": "country",
                "context_label": context_label,
                "trend_label": "growth_7d",
                "trend_value": _to_float(row.get("growth_7d")),
            }
        )

    return {
        "items": items,
        "meta": {
            "country_code": normalized_country_code,
            "country_name": country_name,
            "snapshot_date": snapshot_date,
            "total_ranked_channels": total_ranked_channels,
            "applied_limit": limit,
        },
    }


async def get_category_rankings(
    client: Client,
    *,
    category_slug: str,
    limit: int,
) -> dict[str, Any]:
    normalized_category_slug = category_slug.lower()
    category_response = (
        client.table("categories")
        .select("id, name, slug")
        .eq("slug", normalized_category_slug)
        .limit(1)
        .execute()
    )
    category_rows = category_response.data or []
    if not category_rows:
        return {
            "items": [],
            "meta": {
                "category_slug": normalized_category_slug,
                "category_name": None,
                "snapshot_date": None,
                "total_ranked_channels": 0,
                "applied_limit": limit,
            },
        }

    category = category_rows[0]
    category_id = str(category["id"])
    category_name = category.get("name")

    latest_snapshot_response = (
        client.table("channel_rankings_daily")
        .select("snapshot_date")
        .eq("ranking_scope", "category")
        .eq("category_id", category_id)
        .order("snapshot_date", desc=True)
        .limit(1)
        .execute()
    )
    latest_snapshot_rows = latest_snapshot_response.data or []
    snapshot_date = (
        str(latest_snapshot_rows[0]["snapshot_date"]) if latest_snapshot_rows else None
    )

    if snapshot_date is None:
        return {
            "items": [],
            "meta": {
                "category_slug": normalized_category_slug,
                "category_name": category_name,
                "snapshot_date": None,
                "total_ranked_channels": 0,
                "applied_limit": limit,
            },
        }

    count_response = (
        client.table("channel_rankings_daily")
        .select("id", count="exact", head=True)
        .eq("ranking_scope", "category")
        .eq("category_id", category_id)
        .eq("snapshot_date", snapshot_date)
        .execute()
    )
    total_ranked_channels = int(count_response.count or 0)

    rankings_response = (
        client.table("channel_rankings_daily")
        .select("channel_id, rank, subscribers, growth_7d, engagement_rate")
        .eq("ranking_scope", "category")
        .eq("category_id", category_id)
        .eq("snapshot_date", snapshot_date)
        .order("rank", desc=False)
        .limit(limit)
        .execute()
    )
    ranking_rows = rankings_response.data or []
    channel_ids = [str(row["channel_id"]) for row in ranking_rows if row.get("channel_id")]
    channels_map = _get_channels_map(client, channel_ids)

    items: list[dict[str, Any]] = []
    for row in ranking_rows:
        channel_id = str(row["channel_id"])
        channel_row = channels_map.get(channel_id, {})
        items.append(
            {
                "rank": _to_int(row.get("rank")) or 0,
                "channel_id": channel_id,
                "name": channel_row.get("name") or "Unknown Channel",
                "username": _normalize_username(channel_row.get("username")),
                "subscribers": _to_int(row.get("subscribers")),
                "growth_7d": _to_float(row.get("growth_7d")),
                "engagement_rate": _to_float(row.get("engagement_rate")),
                "context_type": "category",
                "context_label": category_name or normalized_category_slug,
                "trend_label": "engagement_rate",
                "trend_value": _to_float(row.get("engagement_rate")),
            }
        )

    return {
        "items": items,
        "meta": {
            "category_slug": normalized_category_slug,
            "category_name": category_name,
            "snapshot_date": snapshot_date,
            "total_ranked_channels": total_ranked_channels,
            "applied_limit": limit,
        },
    }


async def get_ranking_collections(
    client: Client,
    *,
    limit: int,
) -> dict[str, Any]:
    total_response = (
        client.table("ranking_collections")
        .select("id", count="exact", head=True)
        .eq("is_active", True)
        .execute()
    )
    total_active_collections = int(total_response.count or 0)

    collections_response = (
        client.table("ranking_collections")
        .select("id, slug, name, description, icon")
        .eq("is_active", True)
        .order("name", desc=False)
        .limit(limit)
        .execute()
    )
    collection_rows = collections_response.data or []
    collection_ids = [str(row["id"]) for row in collection_rows if row.get("id")]

    channels_count_map: dict[str, int] = {collection_id: 0 for collection_id in collection_ids}
    if collection_ids:
        links_response = (
            client.table("ranking_collection_channels")
            .select("collection_id")
            .in_("collection_id", collection_ids)
            .execute()
        )
        for row in links_response.data or []:
            collection_id = row.get("collection_id")
            if collection_id is None:
                continue
            collection_id_str = str(collection_id)
            channels_count_map[collection_id_str] = channels_count_map.get(collection_id_str, 0) + 1

    items: list[dict[str, Any]] = []
    for row in collection_rows:
        collection_id = str(row["id"])
        items.append(
            {
                "collection_id": collection_id,
                "slug": row["slug"],
                "name": row["name"],
                "description": row.get("description"),
                "icon": row.get("icon"),
                "channels_count": channels_count_map.get(collection_id, 0),
                "cta_label": "Explore",
                "cta_target": f"/rankings/collections/{collection_id}/channels",
            }
        )

    return {
        "items": items,
        "meta": {
            "total_active_collections": total_active_collections,
            "applied_limit": limit,
        },
    }
