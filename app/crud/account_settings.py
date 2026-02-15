from __future__ import annotations

from supabase import Client


def _to_me_profile(user: dict) -> dict:
    first_name = user.get("first_name")
    last_name = user.get("last_name")
    full_name = " ".join(part for part in [first_name, last_name] if part).strip() or None
    return {
        "user_id": user["id"],
        "first_name": first_name,
        "last_name": last_name,
        "full_name": full_name,
        "email": user.get("email"),
        "telegram_username": user.get("telegram_username"),
        "avatar_url": user.get("avatar_url"),
    }


async def get_me_profile(client: Client, user_id: str) -> dict | None:
    response = client.table("users").select("*").eq("id", user_id).limit(1).execute()
    if not response.data:
        return None
    return _to_me_profile(response.data[0])


async def update_me_profile(client: Client, user_id: str, payload: dict) -> dict | None:
    if payload:
        response = client.table("users").update(payload).eq("id", user_id).execute()
        if not response.data:
            return None

    return await get_me_profile(client, user_id)


async def get_user_preferences(client: Client, user_id: str) -> dict:
    response = (
        client.table("user_preferences")
        .select("language_code, timezone, theme")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    if response.data:
        return response.data[0]

    defaults = {
        "user_id": user_id,
        "language_code": "en",
        "timezone": "UTC",
        "theme": "system",
    }
    created = client.table("user_preferences").insert(defaults).execute()
    return {
        "language_code": created.data[0]["language_code"],
        "timezone": created.data[0]["timezone"],
        "theme": created.data[0]["theme"],
    }


async def update_user_preferences(client: Client, user_id: str, payload: dict) -> dict:
    existing = (
        client.table("user_preferences")
        .select("user_id")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    if existing.data:
        client.table("user_preferences").update(payload).eq("user_id", user_id).execute()
    else:
        insert_payload = {
            "user_id": user_id,
            "language_code": payload.get("language_code", "en"),
            "timezone": payload.get("timezone", "UTC"),
            "theme": payload.get("theme", "system"),
        }
        client.table("user_preferences").insert(insert_payload).execute()

    return await get_user_preferences(client, user_id)


async def get_user_notification_settings(client: Client, user_id: str) -> dict:
    response = (
        client.table("user_notification_settings")
        .select(
            "email_notifications, telegram_bot_alerts, weekly_reports, marketing_updates, push_notifications"
        )
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    if response.data:
        return response.data[0]

    defaults = {
        "user_id": user_id,
        "email_notifications": True,
        "telegram_bot_alerts": True,
        "weekly_reports": False,
        "marketing_updates": False,
        "push_notifications": False,
    }
    created = client.table("user_notification_settings").insert(defaults).execute()
    created_row = created.data[0]
    return {
        "email_notifications": created_row["email_notifications"],
        "telegram_bot_alerts": created_row["telegram_bot_alerts"],
        "weekly_reports": created_row["weekly_reports"],
        "marketing_updates": created_row["marketing_updates"],
        "push_notifications": created_row["push_notifications"],
    }


async def update_user_notification_settings(client: Client, user_id: str, payload: dict) -> dict:
    existing = (
        client.table("user_notification_settings")
        .select("user_id")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    if existing.data:
        client.table("user_notification_settings").update(payload).eq("user_id", user_id).execute()
    else:
        insert_payload = {
            "user_id": user_id,
            "email_notifications": payload.get("email_notifications", True),
            "telegram_bot_alerts": payload.get("telegram_bot_alerts", True),
            "weekly_reports": payload.get("weekly_reports", False),
            "marketing_updates": payload.get("marketing_updates", False),
            "push_notifications": payload.get("push_notifications", False),
        }
        client.table("user_notification_settings").insert(insert_payload).execute()

    return await get_user_notification_settings(client, user_id)
