from fastapi import APIRouter, Depends, HTTPException, Query, status
from supabase import Client

from app.api import deps
from app.crud.mini_app import get_mini_apps_catalog, get_mini_apps_summary
from app.db.base import get_supabase
from app.schemas.mini_app import (
    MiniAppListEnvelope,
    MiniAppListItem,
    MiniAppListMeta,
    MiniAppSortBy,
    MiniAppsPeriod,
    MiniAppsSummary,
    MiniAppsSummaryEnvelope,
    PageResponse,
    SortOrder,
)

router = APIRouter(prefix="/v1.0/mini-apps", tags=["mini_apps"])


@router.get("/summary", response_model=MiniAppsSummaryEnvelope)
async def get_summary(
    period: MiniAppsPeriod = Query(MiniAppsPeriod.D7),
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> MiniAppsSummaryEnvelope:
    _ = current_user
    summary = await get_mini_apps_summary(client, period=period)
    return MiniAppsSummaryEnvelope(data=MiniAppsSummary(**summary), meta={})


@router.get("", response_model=MiniAppListEnvelope)
async def list_mini_apps(
    q: str | None = Query(None, description="Full-text search query"),
    category_slug: str | None = Query(None, description="Category slug filter"),
    min_daily_users: int | None = Query(None, ge=0, description="Minimum daily users"),
    min_rating: float | None = Query(None, ge=0, le=5, description="Minimum rating"),
    launch_within_days: int | None = Query(None, ge=1, description="Launch date filter in days"),
    min_growth: float | None = Query(None, description="Minimum weekly growth percentage"),
    sort_by: MiniAppSortBy = Query(MiniAppSortBy.DAILY_USERS),
    sort_order: SortOrder = Query(SortOrder.DESC),
    limit: int = Query(20, ge=1, le=200),
    cursor: str | None = Query(None),
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> MiniAppListEnvelope:
    _ = current_user

    try:
        result = await get_mini_apps_catalog(
            client,
            q=q,
            category_slug=category_slug,
            min_daily_users=min_daily_users,
            min_rating=min_rating,
            launch_within_days=launch_within_days,
            min_growth=min_growth,
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

    return MiniAppListEnvelope(
        data=[MiniAppListItem(**row) for row in result["items"]],
        page=PageResponse(
            next_cursor=result["next_cursor"],
            has_more=result["has_more"],
        ),
        meta=MiniAppListMeta(total_estimate=result["total_estimate"]),
    )
