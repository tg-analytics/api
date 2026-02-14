from fastapi import APIRouter, Depends, Query
from supabase import Client

from app.api import deps
from app.crud.ranking import (
    get_category_rankings,
    get_country_rankings,
    get_ranking_collections,
)
from app.db.base import get_supabase
from app.schemas.ranking import (
    CategoryRankingsEnvelope,
    CategoryRankingItem,
    CountryRankingsEnvelope,
    CountryRankingItem,
    RankingCollectionItem,
    RankingCollectionsEnvelope,
)

router = APIRouter(prefix="/v1.0/rankings", tags=["rankings"])


@router.get("/countries", response_model=CountryRankingsEnvelope)
async def list_country_rankings(
    country_code: str = Query(
        "US",
        min_length=2,
        max_length=2,
        description="Two-letter country code",
    ),
    limit: int = Query(20, ge=1, le=200),
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> CountryRankingsEnvelope:
    _ = current_user
    result = await get_country_rankings(client, country_code=country_code, limit=limit)
    return CountryRankingsEnvelope(
        data=[CountryRankingItem(**item) for item in result["items"]],
        meta=result["meta"],
    )


@router.get("/categories", response_model=CategoryRankingsEnvelope)
async def list_category_rankings(
    category_slug: str = Query("technology", description="Category slug"),
    limit: int = Query(20, ge=1, le=200),
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> CategoryRankingsEnvelope:
    _ = current_user
    result = await get_category_rankings(
        client,
        category_slug=category_slug,
        limit=limit,
    )
    return CategoryRankingsEnvelope(
        data=[CategoryRankingItem(**item) for item in result["items"]],
        meta=result["meta"],
    )


@router.get("/collections", response_model=RankingCollectionsEnvelope)
async def list_ranking_collections(
    limit: int = Query(20, ge=1, le=200),
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> RankingCollectionsEnvelope:
    _ = current_user
    result = await get_ranking_collections(client, limit=limit)
    return RankingCollectionsEnvelope(
        data=[RankingCollectionItem(**item) for item in result["items"]],
        meta=result["meta"],
    )
