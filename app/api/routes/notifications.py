from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.api import deps
from app.crud.notification import (
    get_user_notification_by_id,
    get_user_notifications,
    mark_all_notifications_as_read,
    mark_notification_as_read,
)
from app.db.base import get_supabase
from app.schemas.notification import NotificationResponse

router = APIRouter(prefix="/v1.0/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationResponse])
async def list_notifications(
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> list[NotificationResponse]:
    """List notifications for the current user."""
    notifications = await get_user_notifications(client, current_user["id"])
    return [NotificationResponse(**notification) for notification in notifications]


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: str,
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> NotificationResponse:
    """Retrieve a single notification for the current user."""
    notification = await get_user_notification_by_id(
        client, notification_id=notification_id, user_id=current_user["id"]
    )
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )
    return NotificationResponse(**notification)


@router.post("/read", response_model=list[NotificationResponse])
async def mark_all_notifications_read(
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> list[NotificationResponse]:
    """Mark all notifications for the current user as read."""
    notifications = await mark_all_notifications_as_read(client, current_user["id"])
    return [NotificationResponse(**notification) for notification in notifications]


@router.post("/{notification_id}/read", response_model=NotificationResponse)
async def mark_single_notification_read(
    notification_id: str,
    current_user: dict = Depends(deps.get_current_user),
    client: Client = Depends(get_supabase),
) -> NotificationResponse:
    """Mark a single notification as read for the current user."""
    existing = await get_user_notification_by_id(
        client, notification_id=notification_id, user_id=current_user["id"]
    )
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    updated = await mark_notification_as_read(
        client, notification_id=notification_id, user_id=current_user["id"]
    )
    return NotificationResponse(**updated)
