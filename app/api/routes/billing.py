from datetime import date

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from supabase import Client

from app.api import deps
from app.crud.account_access import ensure_account_access
from app.crud.billing import (
    add_payment_method,
    get_account_usage,
    get_invoice_download,
    get_subscription,
    list_invoices,
    list_payment_methods,
    update_subscription,
)
from app.db.base import get_supabase
from app.schemas.account_settings import (
    AccountUsage,
    AccountUsageEnvelope,
    Invoice,
    InvoiceDownload,
    InvoiceDownloadEnvelope,
    InvoiceListEnvelope,
    PageResponse,
    PaymentMethod,
    PaymentMethodCreateRequest,
    PaymentMethodEnvelope,
    PaymentMethodListEnvelope,
    Subscription,
    SubscriptionEnvelope,
    SubscriptionUpdateRequest,
)

router = APIRouter(prefix="/v1.0/accounts/{account_id}", tags=["billing"])


@router.get("/subscription", response_model=SubscriptionEnvelope)
async def get_account_subscription(
    account_id: str,
    x_account_id: str = Header(..., alias="X-Account-Id"),
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> SubscriptionEnvelope:
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

    subscription = await get_subscription(client, account_id=account_id)
    if subscription is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found.")

    return SubscriptionEnvelope(data=Subscription(**subscription), meta={})


@router.patch("/subscription", response_model=SubscriptionEnvelope)
async def patch_account_subscription(
    account_id: str,
    payload: SubscriptionUpdateRequest,
    x_account_id: str = Header(..., alias="X-Account-Id"),
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> SubscriptionEnvelope:
    try:
        await ensure_account_access(
            client,
            account_id=account_id,
            header_account_id=x_account_id,
            user_id=current_user["id"],
            require_write=True,
        )
        updated = await update_subscription(
            client,
            account_id=account_id,
            user_id=current_user["id"],
            plan_code=payload.plan_code,
            cancel_at_period_end=payload.cancel_at_period_end,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found.")

    return SubscriptionEnvelope(data=Subscription(**updated), meta={})


@router.get("/usage", response_model=AccountUsageEnvelope)
async def get_usage(
    account_id: str,
    x_account_id: str = Header(..., alias="X-Account-Id"),
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> AccountUsageEnvelope:
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

    usage = await get_account_usage(
        client,
        account_id=account_id,
        from_date=from_date,
        to_date=to_date,
    )
    return AccountUsageEnvelope(data=AccountUsage(**usage), meta={})


@router.get("/payment-methods", response_model=PaymentMethodListEnvelope)
async def get_payment_methods(
    account_id: str,
    x_account_id: str = Header(..., alias="X-Account-Id"),
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> PaymentMethodListEnvelope:
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

    items = await list_payment_methods(client, account_id=account_id)
    return PaymentMethodListEnvelope(data=[PaymentMethod(**item) for item in items], meta={})


@router.post("/payment-methods", response_model=PaymentMethodEnvelope, status_code=status.HTTP_201_CREATED)
async def post_payment_method(
    account_id: str,
    payload: PaymentMethodCreateRequest,
    x_account_id: str = Header(..., alias="X-Account-Id"),
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> PaymentMethodEnvelope:
    try:
        await ensure_account_access(
            client,
            account_id=account_id,
            header_account_id=x_account_id,
            user_id=current_user["id"],
            require_write=True,
        )
        item = await add_payment_method(
            client,
            account_id=account_id,
            token=payload.provider_payment_method_token,
            make_default=payload.make_default,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return PaymentMethodEnvelope(data=PaymentMethod(**item), meta={})


@router.get("/invoices", response_model=InvoiceListEnvelope)
async def get_invoices(
    account_id: str,
    x_account_id: str = Header(..., alias="X-Account-Id"),
    limit: int = Query(20, ge=1, le=200),
    cursor: str | None = Query(None),
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> InvoiceListEnvelope:
    try:
        await ensure_account_access(
            client,
            account_id=account_id,
            header_account_id=x_account_id,
            user_id=current_user["id"],
            require_write=False,
        )
        result = await list_invoices(client, account_id=account_id, limit=limit, cursor=cursor)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return InvoiceListEnvelope(
        data=[Invoice(**item) for item in result["items"]],
        page=PageResponse(next_cursor=result["next_cursor"], has_more=result["has_more"]),
        meta={},
    )


@router.get("/invoices/{invoice_id}/download-url", response_model=InvoiceDownloadEnvelope)
async def get_invoice_download_url(
    account_id: str,
    invoice_id: str,
    x_account_id: str = Header(..., alias="X-Account-Id"),
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> InvoiceDownloadEnvelope:
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

    item = await get_invoice_download(client, account_id=account_id, invoice_id=invoice_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found.")

    return InvoiceDownloadEnvelope(data=InvoiceDownload(**item), meta={})
