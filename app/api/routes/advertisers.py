from fastapi import APIRouter, Depends, HTTPException, Query, status
from supabase import Client

from app.api import deps
from app.crud.advertiser import (
    get_advertiser_detail,
    get_advertisers_catalog,
    get_advertisers_summary,
)
from app.db.base import get_supabase
from app.schemas.advertiser import (
    AdvertiserActivityStatus,
    AdvertiserDetail,
    AdvertiserDetailEnvelope,
    AdvertiserDetailMeta,
    AdvertiserListEnvelope,
    AdvertiserListItem,
    AdvertiserListMeta,
    AdvertiserSortBy,
    AdvertiserSummary,
    AdvertiserSummaryEnvelope,
    AdvertiserSummaryMeta,
    AdvertiserTimePeriodDays,
    PageResponse,
    SortOrder,
)

router = APIRouter(prefix="/v1.0/advertisers", tags=["advertisers"])


@router.get("", response_model=AdvertiserListEnvelope)
async def list_advertisers(
    q: str | None = Query(None, description="Full-text search query"),
    industry_slug: str | None = Query(None, description="Industry slug filter"),
    time_period_days: AdvertiserTimePeriodDays = Query(AdvertiserTimePeriodDays.D30),
    min_spend: float | None = Query(None, ge=0, description="Minimum estimated spend"),
    min_channels: int | None = Query(None, ge=0, description="Minimum channels used"),
    min_engagement: float | None = Query(None, ge=0, le=100, description="Minimum engagement rate"),
    activity_status: AdvertiserActivityStatus = Query(AdvertiserActivityStatus.ALL),
    sort_by: AdvertiserSortBy = Query(AdvertiserSortBy.ESTIMATED_SPEND),
    sort_order: SortOrder = Query(SortOrder.DESC),
    limit: int = Query(20, ge=1, le=200),
    cursor: str | None = Query(None),
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> AdvertiserListEnvelope:
    _ = current_user

    try:
        result = await get_advertisers_catalog(
            client,
            q=q,
            industry_slug=industry_slug,
            time_period_days=int(time_period_days),
            min_spend=min_spend,
            min_channels=min_channels,
            min_engagement=min_engagement,
            activity_status=activity_status,
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

    return AdvertiserListEnvelope(
        data=[AdvertiserListItem(**row) for row in result["items"]],
        page=PageResponse(
            next_cursor=result["next_cursor"],
            has_more=result["has_more"],
        ),
        meta=AdvertiserListMeta(
            total_estimate=result["total_estimate"],
            time_period_days=int(time_period_days),
            snapshot_date=result["snapshot_date"],
            baseline_date=result["baseline_date"],
        ),
    )


@router.get("/summary", response_model=AdvertiserSummaryEnvelope)
async def get_summary(
    time_period_days: AdvertiserTimePeriodDays = Query(AdvertiserTimePeriodDays.D30),
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> AdvertiserSummaryEnvelope:
    _ = current_user
    summary = await get_advertisers_summary(client, time_period_days=int(time_period_days))
    return AdvertiserSummaryEnvelope(
        data=AdvertiserSummary(
            active_advertisers=summary["active_advertisers"],
            total_ad_spend=summary["total_ad_spend"],
            ad_campaigns=summary["ad_campaigns"],
            avg_engagement_rate=summary["avg_engagement_rate"],
            active_advertisers_delta=summary["active_advertisers_delta"],
            total_ad_spend_delta=summary["total_ad_spend_delta"],
            total_ad_spend_delta_percent=summary["total_ad_spend_delta_percent"],
            ad_campaigns_delta=summary["ad_campaigns_delta"],
            ad_campaigns_delta_percent=summary["ad_campaigns_delta_percent"],
            avg_engagement_rate_delta=summary["avg_engagement_rate_delta"],
            avg_engagement_rate_delta_percent=summary["avg_engagement_rate_delta_percent"],
        ),
        meta=AdvertiserSummaryMeta(
            time_period_days=int(time_period_days),
            snapshot_date=summary["snapshot_date"],
            baseline_date=summary["baseline_date"],
        ),
    )


@router.get("/{advertiser_id}", response_model=AdvertiserDetailEnvelope)
async def get_advertiser(
    advertiser_id: str,
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> AdvertiserDetailEnvelope:
    _ = current_user
    advertiser = await get_advertiser_detail(client, advertiser_id=advertiser_id)
    if advertiser is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Advertiser not found",
        )

    return AdvertiserDetailEnvelope(
        data=AdvertiserDetail(
            advertiser_id=advertiser["advertiser_id"],
            name=advertiser["name"],
            slug=advertiser["slug"],
            logo_url=advertiser.get("logo_url"),
            industry_slug=advertiser.get("industry_slug"),
            industry_name=advertiser.get("industry_name"),
            estimated_spend=advertiser.get("estimated_spend"),
            total_ads=advertiser.get("total_ads"),
            channels_used=advertiser.get("channels_used"),
            avg_engagement_rate=advertiser.get("avg_engagement_rate"),
            trend=advertiser.get("trend"),
            active_creatives=advertiser.get("active_creatives"),
            last_active_at=advertiser.get("last_active_at"),
            website_url=advertiser.get("website_url"),
            description=advertiser.get("description"),
            top_channels=advertiser.get("top_channels", []),
        ),
        meta=AdvertiserDetailMeta(snapshot_date=advertiser.get("snapshot_date")),
    )
