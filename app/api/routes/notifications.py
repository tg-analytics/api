from fastapi import APIRouter, Depends
from supabase import Client

from app.api import deps
from app.crud.notification import get_user_notifications
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
