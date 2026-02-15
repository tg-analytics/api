from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from supabase import Client

from app.api import deps
from app.crud.tracker import (
    create_tracker,
    delete_tracker,
    ensure_account_access,
    list_tracker_mentions,
    list_trackers,
    update_tracker,
)
from app.db.base import get_supabase
from app.schemas.tracker import (
    PageResponse,
    Tracker,
    TrackerCreateRequest,
    TrackerEnvelope,
    TrackerListEnvelope,
    TrackerMention,
    TrackerMentionListEnvelope,
    TrackerStatus,
    TrackerType,
    TrackerUpdateRequest,
)

router = APIRouter(prefix="/v1.0/accounts/{account_id}", tags=["trackers"])


@router.get("/trackers", response_model=TrackerListEnvelope)
async def get_trackers(
    account_id: str,
    x_account_id: str = Header(..., alias="X-Account-Id"),
    status_filter: TrackerStatus | None = Query(None, alias="status"),
    tracker_type: TrackerType | None = Query(None, alias="type"),
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> TrackerListEnvelope:
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

    items = await list_trackers(
        client,
        account_id=account_id,
        status=status_filter,
        tracker_type=tracker_type,
    )
    return TrackerListEnvelope(data=[Tracker(**row) for row in items], meta={})


@router.post("/trackers", response_model=TrackerEnvelope, status_code=status.HTTP_201_CREATED)
async def post_tracker(
    account_id: str,
    payload: TrackerCreateRequest,
    x_account_id: str = Header(..., alias="X-Account-Id"),
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> TrackerEnvelope:
    try:
        await ensure_account_access(
            client,
            account_id=account_id,
            header_account_id=x_account_id,
            user_id=current_user["id"],
            require_write=True,
        )
        created = await create_tracker(
            client,
            account_id=account_id,
            user_id=current_user["id"],
            tracker_type=payload.tracker_type,
            tracker_value=payload.tracker_value,
            notify_push=payload.notify_push,
            notify_telegram=payload.notify_telegram,
            notify_email=payload.notify_email,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return TrackerEnvelope(data=Tracker(**created), meta={})


@router.patch("/trackers/{tracker_id}", response_model=TrackerEnvelope)
async def patch_tracker(
    account_id: str,
    tracker_id: str,
    payload: TrackerUpdateRequest,
    x_account_id: str = Header(..., alias="X-Account-Id"),
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> TrackerEnvelope:
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

    updated = await update_tracker(
        client,
        account_id=account_id,
        tracker_id=tracker_id,
        user_id=current_user["id"],
        status=payload.status,
        notify_push=payload.notify_push,
        notify_telegram=payload.notify_telegram,
        notify_email=payload.notify_email,
    )
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tracker not found.")

    return TrackerEnvelope(data=Tracker(**updated), meta={})


@router.delete("/trackers/{tracker_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_tracker(
    account_id: str,
    tracker_id: str,
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

    deleted = await delete_tracker(
        client,
        account_id=account_id,
        tracker_id=tracker_id,
        user_id=current_user["id"],
    )
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tracker not found.")

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/tracker-mentions", response_model=TrackerMentionListEnvelope)
async def get_mentions(
    account_id: str,
    x_account_id: str = Header(..., alias="X-Account-Id"),
    tracker_id: str | None = Query(None),
    since: datetime | None = Query(None),
    until: datetime | None = Query(None),
    limit: int = Query(20, ge=1, le=200),
    cursor: str | None = Query(None),
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> TrackerMentionListEnvelope:
    if since is not None and until is not None and since > until:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="since must be less than or equal to until",
        )

    try:
        await ensure_account_access(
            client,
            account_id=account_id,
            header_account_id=x_account_id,
            user_id=current_user["id"],
            require_write=False,
        )
        result = await list_tracker_mentions(
            client,
            account_id=account_id,
            tracker_id=tracker_id,
            since=since,
            until=until,
            limit=limit,
            cursor=cursor,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return TrackerMentionListEnvelope(
        data=[TrackerMention(**row) for row in result["items"]],
        page=PageResponse(next_cursor=result["next_cursor"], has_more=result["has_more"]),
        meta={},
    )
