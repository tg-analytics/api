from supabase import Client


async def create_notification(
    client: Client, *, user_id: str, subject: str, body: str
) -> dict:
    """Create a notification record for a user."""
    notification_data = {
        "user_id": user_id,
        "subject": subject,
        "body": body,
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
