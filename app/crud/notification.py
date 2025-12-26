from datetime import UTC, datetime

from supabase import Client

from app.schemas.notification import NotificationType


async def create_notification(
    client: Client,
    *,
    user_id: str,
    subject: str,
    body: str,
    notification_type: NotificationType | str = NotificationType.WELCOME,
    details: str | None = None,
    cta: str | None = None,
) -> dict:
    """Create a notification record for a user."""
    notification_data = {
        "user_id": user_id,
        "subject": subject,
        "body": body,
        "type": (
            notification_type.value
            if isinstance(notification_type, NotificationType)
            else notification_type
        ),
        "details": details,
        "cta": cta,
    }

    response = client.table("notifications").insert(notification_data).execute()

    if not response.data or len(response.data) == 0:
        raise ValueError("Failed to create notification")

    return response.data[0]


async def get_user_notification_by_subject(
    client: Client, *, user_id: str, subject: str
) -> dict | None:
    """Get a notification for a user that matches the given subject."""
    response = (
        client.table("notifications")
        .select("*")
        .eq("user_id", user_id)
        .eq("subject", subject)
        .is_("deleted_at", "null")
        .limit(1)
        .execute()
    )

    if response.data and len(response.data) > 0:
        return response.data[0]
    return None


async def get_user_notifications(client: Client, user_id: str) -> list[dict]:
    """Get all non-deleted notifications for a user ordered by newest first."""
    response = (
        client.table("notifications")
        .select("*")
        .eq("user_id", user_id)
        .is_("deleted_at", "null")
        .order("created_at", desc=True)
        .execute()
    )

    return response.data or []


async def get_user_notification_by_id(
    client: Client, *, notification_id: str, user_id: str
) -> dict | None:
    """Get a specific notification for a user if it exists."""
    response = (
        client.table("notifications")
        .select("*")
        .eq("id", notification_id)
        .eq("user_id", user_id)
        .is_("deleted_at", "null")
        .limit(1)
        .execute()
    )

    if response.data:
        return response.data[0]
    return None


async def mark_all_notifications_as_read(client: Client, user_id: str) -> list[dict]:
    """Mark all non-deleted notifications for a user as read."""
    read_at = datetime.now(UTC).isoformat()
    response = (
        client.table("notifications")
        .update({"is_read": True, "read_at": read_at})
        .eq("user_id", user_id)
        .is_("deleted_at", "null")
        .execute()
    )

    return response.data or []


async def mark_notification_as_read(client: Client, *, notification_id: str, user_id: str) -> dict:
    """Mark a single notification as read for a user."""
    read_at = datetime.now(UTC).isoformat()
    response = (
        client.table("notifications")
        .update({"is_read": True, "read_at": read_at})
        .eq("id", notification_id)
        .eq("user_id", user_id)
        .is_("deleted_at", "null")
        .limit(1)
        .execute()
    )

    if not response.data:
        raise ValueError("Notification not found")

    return response.data[0]
