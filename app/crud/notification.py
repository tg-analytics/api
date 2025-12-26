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
