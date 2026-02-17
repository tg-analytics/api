from fastapi import APIRouter, Depends, HTTPException, Query, status
from supabase import Client

from app.crud.home import get_home_categories, get_home_countries
from app.db.base import get_supabase
from app.schemas.home import (
    HomeCategoriesEnvelope,
    HomeCategoriesMeta,
    HomeCategoryItem,
    HomeCountriesEnvelope,
    HomeCountriesMeta,
    HomeCountryItem,
    PageResponse,
)

router = APIRouter(prefix="/v1.0/home", tags=["home"])


@router.get("/categories", response_model=HomeCategoriesEnvelope)
async def list_home_categories(
    limit: int = Query(20, ge=1, le=200),
    cursor: str | None = Query(None),
    client: Client = Depends(get_supabase),
) -> HomeCategoriesEnvelope:
    try:
        result = await get_home_categories(
            client,
            limit=limit,
            cursor=cursor,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return HomeCategoriesEnvelope(
        data=[HomeCategoryItem(**row) for row in result["items"]],
        page=PageResponse(
            next_cursor=result["next_cursor"],
            has_more=result["has_more"],
        ),
        meta=HomeCategoriesMeta(total_estimate=result["total_estimate"]),
    )


@router.get("/countries", response_model=HomeCountriesEnvelope)
async def list_home_countries(
    limit: int = Query(20, ge=1, le=200),
    cursor: str | None = Query(None),
    client: Client = Depends(get_supabase),
) -> HomeCountriesEnvelope:
    try:
        result = await get_home_countries(
            client,
            limit=limit,
            cursor=cursor,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return HomeCountriesEnvelope(
        data=[HomeCountryItem(**row) for row in result["items"]],
        page=PageResponse(
            next_cursor=result["next_cursor"],
            has_more=result["has_more"],
        ),
        meta=HomeCountriesMeta(total_estimate=result["total_estimate"]),
    )
