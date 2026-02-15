from datetime import date

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from supabase import Client

from app.api import deps
from app.crud.account_access import ensure_account_access
from app.crud.api_keys import create_api_key, get_api_usage, list_api_keys, revoke_api_key, rotate_api_key
from app.db.base import get_supabase
from app.schemas.account_settings import (
    ApiKeyCreateEnvelope,
    ApiKeyCreateRequest,
    ApiKeyCreateResponse,
    ApiKeyListEnvelope,
    ApiKeyListItem,
    ApiUsage,
    ApiUsageEnvelope,
)

router = APIRouter(prefix="/v1.0/accounts/{account_id}", tags=["api_keys"])


@router.get("/api-keys", response_model=ApiKeyListEnvelope)
async def get_api_keys(
    account_id: str,
    x_account_id: str = Header(..., alias="X-Account-Id"),
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> ApiKeyListEnvelope:
    try:
        await ensure_account_access(
            client,
            account_id=account_id,
            header_account_id=x_account_id,
            user_id=current_user["id"],
            require_write=False,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    items = await list_api_keys(client, account_id=account_id)
    return ApiKeyListEnvelope(data=[ApiKeyListItem(**item) for item in items], meta={})


@router.post("/api-keys", response_model=ApiKeyCreateEnvelope, status_code=status.HTTP_201_CREATED)
async def post_api_key(
    account_id: str,
    payload: ApiKeyCreateRequest,
    x_account_id: str = Header(..., alias="X-Account-Id"),
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> ApiKeyCreateEnvelope:
    try:
        await ensure_account_access(
            client,
            account_id=account_id,
            header_account_id=x_account_id,
            user_id=current_user["id"],
            require_write=True,
        )
        created = await create_api_key(
            client,
            account_id=account_id,
            user_id=current_user["id"],
            name=payload.name,
            scopes=payload.scopes,
            rate_limit_per_hour=payload.rate_limit_per_hour,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return ApiKeyCreateEnvelope(data=ApiKeyCreateResponse(**created), meta={"secret_returned_once": True})


@router.post("/api-keys/{api_key_id}/rotate", response_model=ApiKeyCreateEnvelope)
async def post_rotate_api_key(
    account_id: str,
    api_key_id: str,
    x_account_id: str = Header(..., alias="X-Account-Id"),
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> ApiKeyCreateEnvelope:
    try:
        await ensure_account_access(
            client,
            account_id=account_id,
            header_account_id=x_account_id,
            user_id=current_user["id"],
            require_write=True,
        )
        rotated = await rotate_api_key(
            client,
            account_id=account_id,
            api_key_id=api_key_id,
            user_id=current_user["id"],
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    if rotated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found.")

    return ApiKeyCreateEnvelope(data=ApiKeyCreateResponse(**rotated), meta={"secret_returned_once": True})


@router.delete("/api-keys/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    account_id: str,
    api_key_id: str,
    x_account_id: str = Header(..., alias="X-Account-Id"),
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> Response:
    try:
        await ensure_account_access(
            client,
            account_id=account_id,
            header_account_id=x_account_id,
            user_id=current_user["id"],
            require_write=True,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    revoked = await revoke_api_key(
        client,
        account_id=account_id,
        api_key_id=api_key_id,
        user_id=current_user["id"],
    )
    if not revoked:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found.")

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/api-usage", response_model=ApiUsageEnvelope)
async def get_account_api_usage(
    account_id: str,
    x_account_id: str = Header(..., alias="X-Account-Id"),
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> ApiUsageEnvelope:
    if from_date is not None and to_date is not None and from_date > to_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="from must be <= to")

    try:
        await ensure_account_access(
            client,
            account_id=account_id,
            header_account_id=x_account_id,
            user_id=current_user["id"],
            require_write=False,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    usage = await get_api_usage(
        client,
        account_id=account_id,
        from_date=from_date,
        to_date=to_date,
    )
    return ApiUsageEnvelope(data=ApiUsage(**usage), meta={})
