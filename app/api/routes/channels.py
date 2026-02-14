from fastapi import APIRouter, Depends, HTTPException, Query, status
from supabase import Client

from app.api import deps
from app.crud.channel import get_catalog_channels, get_channel_overview
from app.db.base import get_supabase
from app.schemas.channel import (
    ChannelListEnvelope,
    ChannelListItem,
    ChannelListMeta,
    ChannelOverviewEnvelope,
    ChannelSizeBucket,
    ChannelSortBy,
    ChannelStatus,
    PageResponse,
    SortOrder,
)

router = APIRouter(prefix="/v1.0/channels", tags=["channels"])


@router.get("", response_model=ChannelListEnvelope)
async def list_channels(
    q: str | None = Query(None, description="Full-text search query"),
    country_code: str | None = Query(
        None,
        min_length=2,
        max_length=2,
        description="Two-letter country code",
    ),
    category_slug: str | None = Query(None, description="Category slug filter"),
    size_bucket: ChannelSizeBucket | None = Query(None, description="Audience size bucket"),
    er_min: float | None = Query(None, ge=0, le=100, description="Minimum engagement rate"),
    er_max: float | None = Query(None, ge=0, le=100, description="Maximum engagement rate"),
    status_filter: ChannelStatus | None = Query(None, alias="status", description="Status filter"),
    verified: bool | None = Query(None, description="Verified channels only"),
    scam: bool | None = Query(None, description="Scam channels only"),
    sort_by: ChannelSortBy = Query(ChannelSortBy.SUBSCRIBERS),
    sort_order: SortOrder = Query(SortOrder.DESC),
    limit: int = Query(20, ge=1, le=200),
    cursor: str | None = Query(None),
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> ChannelListEnvelope:
    """Search and filter channels catalog."""
    _ = current_user

    if er_min is not None and er_max is not None and er_min > er_max:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="er_min cannot be greater than er_max",
        )

    try:
        result = await get_catalog_channels(
            client,
            q=q,
            country_code=country_code,
            category_slug=category_slug,
            size_bucket=size_bucket,
            er_min=er_min,
            er_max=er_max,
            status=status_filter,
            verified=verified,
            scam=scam,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            cursor=cursor,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return ChannelListEnvelope(
        data=[ChannelListItem(**row) for row in result["items"]],
        page=PageResponse(
            next_cursor=result["next_cursor"],
            has_more=result["has_more"],
        ),
        meta=ChannelListMeta(total_estimate=result["total_estimate"]),
    )


@router.get("/{channel_id}/overview", response_model=ChannelOverviewEnvelope)
async def get_channel_overview_page(
    channel_id: str,
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> ChannelOverviewEnvelope:
    _ = current_user
    overview = await get_channel_overview(client, channel_id)
    if overview is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found",
        )

    return ChannelOverviewEnvelope(data=overview, meta={})
