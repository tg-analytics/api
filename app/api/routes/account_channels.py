from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from supabase import Client

from app.api import deps
from app.crud.account_access import ensure_account_access
from app.crud.account_channels import (
    add_account_channel,
    confirm_verification_request,
    create_verification_request,
    get_account_channel_insights,
    list_account_channels,
)
from app.db.base import get_supabase
from app.schemas.account_settings import (
    AccountChannel,
    AccountChannelEnvelope,
    AccountChannelInsights,
    AccountChannelInsightsEnvelope,
    AccountChannelListEnvelope,
    AddAccountChannelRequest,
    PageResponse,
    VerificationConfirmRequest,
    VerificationRequest,
    VerificationRequestCreateRequest,
    VerificationRequestEnvelope,
)

router = APIRouter(prefix="/v1.0/accounts/{account_id}", tags=["account_channels"])


@router.get("/channels", response_model=AccountChannelListEnvelope)
async def get_account_channels(
    account_id: str,
    x_account_id: str = Header(..., alias="X-Account-Id"),
    limit: int = Query(20, ge=1, le=200),
    cursor: str | None = Query(None),
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> AccountChannelListEnvelope:
    try:
        await ensure_account_access(
            client,
            account_id=account_id,
            header_account_id=x_account_id,
            user_id=current_user["id"],
            require_write=False,
        )
        result = await list_account_channels(
            client,
            account_id=account_id,
            limit=limit,
            cursor=cursor,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return AccountChannelListEnvelope(
        data=[AccountChannel(**item) for item in result["items"]],
        page=PageResponse(next_cursor=result["next_cursor"], has_more=result["has_more"]),
        meta={},
    )


@router.post("/channels", response_model=AccountChannelEnvelope, status_code=status.HTTP_201_CREATED)
async def post_account_channel(
    account_id: str,
    payload: AddAccountChannelRequest,
    x_account_id: str = Header(..., alias="X-Account-Id"),
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> AccountChannelEnvelope:
    try:
        await ensure_account_access(
            client,
            account_id=account_id,
            header_account_id=x_account_id,
            user_id=current_user["id"],
            require_write=True,
        )
        created = await add_account_channel(
            client,
            account_id=account_id,
            user_id=current_user["id"],
            channel_id=payload.channel_id,
            alias_name=payload.alias_name,
            monitoring_enabled=payload.monitoring_enabled,
            is_favorite=payload.is_favorite,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return AccountChannelEnvelope(data=AccountChannel(**created), meta={})


@router.get("/channels/insights", response_model=AccountChannelInsightsEnvelope)
async def get_channels_insights(
    account_id: str,
    x_account_id: str = Header(..., alias="X-Account-Id"),
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> AccountChannelInsightsEnvelope:
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

    insights = await get_account_channel_insights(client, account_id=account_id)
    return AccountChannelInsightsEnvelope(data=AccountChannelInsights(**insights), meta={})


@router.post(
    "/channels/{channel_id}/verification",
    response_model=VerificationRequestEnvelope,
    status_code=status.HTTP_201_CREATED,
)
async def post_channel_verification(
    account_id: str,
    channel_id: str,
    payload: VerificationRequestCreateRequest,
    x_account_id: str = Header(..., alias="X-Account-Id"),
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> VerificationRequestEnvelope:
    try:
        await ensure_account_access(
            client,
            account_id=account_id,
            header_account_id=x_account_id,
            user_id=current_user["id"],
            require_write=True,
        )
        created = await create_verification_request(
            client,
            account_id=account_id,
            channel_id=channel_id,
            user_id=current_user["id"],
            verification_method=payload.verification_method,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return VerificationRequestEnvelope(data=VerificationRequest(**created), meta={})


@router.post(
    "/channels/{channel_id}/verification/{request_id}/confirm",
    response_model=VerificationRequestEnvelope,
)
async def post_confirm_verification(
    account_id: str,
    channel_id: str,
    request_id: str,
    payload: VerificationConfirmRequest,
    x_account_id: str = Header(..., alias="X-Account-Id"),
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> VerificationRequestEnvelope:
    try:
        await ensure_account_access(
            client,
            account_id=account_id,
            header_account_id=x_account_id,
            user_id=current_user["id"],
            require_write=True,
        )
        updated = await confirm_verification_request(
            client,
            account_id=account_id,
            channel_id=channel_id,
            request_id=request_id,
            user_id=current_user["id"],
            evidence=payload.evidence,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Verification request not found.")

    return VerificationRequestEnvelope(data=VerificationRequest(**updated), meta={})
