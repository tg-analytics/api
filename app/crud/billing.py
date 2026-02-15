from __future__ import annotations

import json
from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import UTC, date, datetime, timedelta
from secrets import token_hex
from typing import Any

from supabase import Client


def _encode_cursor(last_invoice_id: str) -> str:
    payload = json.dumps({"invoice_id": last_invoice_id}).encode("utf-8")
    return urlsafe_b64encode(payload).decode("utf-8")


def _decode_cursor(cursor: str) -> str:
    try:
        payload = json.loads(urlsafe_b64decode(cursor).decode("utf-8"))
        invoice_id = str(payload["invoice_id"])
    except Exception as exc:  # noqa: BLE001
        raise ValueError("Invalid pagination cursor") from exc
    if not invoice_id:
        raise ValueError("Invalid pagination cursor")
    return invoice_id


async def get_subscription(client: Client, *, account_id: str) -> dict[str, Any] | None:
    response = (
        client.table("account_subscriptions")
        .select("*")
        .eq("account_id", account_id)
        .limit(1)
        .execute()
    )
    if not response.data:
        return None

    row = response.data[0]
    plan_response = client.table("billing_plans").select("code").eq("id", row["plan_id"]).limit(1).execute()
    plan_code = plan_response.data[0]["code"] if plan_response.data else "unknown"

    return {
        "subscription_id": row["id"],
        "account_id": row["account_id"],
        "plan_code": plan_code,
        "status": row["status"],
        "billing_state": row["billing_state"],
        "current_period_start": row.get("current_period_start"),
        "current_period_end": row.get("current_period_end"),
        "cancel_at_period_end": bool(row.get("cancel_at_period_end", False)),
    }


async def update_subscription(
    client: Client,
    *,
    account_id: str,
    user_id: str,
    plan_code: str | None,
    cancel_at_period_end: bool | None,
) -> dict[str, Any] | None:
    existing = (
        client.table("account_subscriptions")
        .select("*")
        .eq("account_id", account_id)
        .limit(1)
        .execute()
    )
    if not existing.data:
        return None

    update_payload: dict[str, Any] = {}

    if plan_code is not None:
        plan = (
            client.table("billing_plans")
            .select("id")
            .eq("code", plan_code)
            .eq("is_active", True)
            .limit(1)
            .execute()
        )
        if not plan.data:
            raise ValueError("Unknown plan_code")
        update_payload["plan_id"] = plan.data[0]["id"]

    if cancel_at_period_end is not None:
        update_payload["cancel_at_period_end"] = cancel_at_period_end

    if update_payload:
        update_payload["updated_by"] = user_id
        client.table("account_subscriptions").update(update_payload).eq("account_id", account_id).execute()

    return await get_subscription(client, account_id=account_id)


async def get_account_usage(
    client: Client,
    *,
    account_id: str,
    from_date: date | None,
    to_date: date | None,
) -> dict[str, Any]:
    today = date.today()
    start = from_date or (today - timedelta(days=29))
    end = to_date or today

    usage_rows = (
        client.table("account_usage_daily")
        .select("channel_searches, event_trackers_count, api_requests_count, exports_count")
        .eq("account_id", account_id)
        .gte("usage_date", start.isoformat())
        .lte("usage_date", end.isoformat())
        .execute()
    ).data or []

    return {
        "from": start,
        "to": end,
        "channel_searches": sum(int(row.get("channel_searches") or 0) for row in usage_rows),
        "event_trackers_count": sum(int(row.get("event_trackers_count") or 0) for row in usage_rows),
        "api_requests_count": sum(int(row.get("api_requests_count") or 0) for row in usage_rows),
        "exports_count": sum(int(row.get("exports_count") or 0) for row in usage_rows),
    }


async def list_payment_methods(client: Client, *, account_id: str) -> list[dict[str, Any]]:
    rows = (
        client.table("payment_methods")
        .select("*")
        .eq("account_id", account_id)
        .order("is_default", desc=True)
        .order("created_at", desc=True)
        .execute()
    ).data or []

    return [
        {
            "payment_method_id": row["id"],
            "brand": row.get("brand"),
            "last4": row.get("last4"),
            "exp_month": row.get("exp_month"),
            "exp_year": row.get("exp_year"),
            "is_default": bool(row.get("is_default", False)),
            "status": row.get("status", "active"),
        }
        for row in rows
    ]


async def add_payment_method(
    client: Client,
    *,
    account_id: str,
    token: str,
    make_default: bool,
) -> dict[str, Any]:
    if not token.startswith("pm_"):
        raise ValueError("Payment provider token invalid.")

    if make_default:
        client.table("payment_methods").update({"is_default": False}).eq("account_id", account_id).execute()

    digits = "".join([ch for ch in token if ch.isdigit()])
    last4 = (digits[-4:] if len(digits) >= 4 else token_hex(2)).upper()
    now = datetime.now(UTC)

    payload = {
        "account_id": account_id,
        "provider_payment_method_id": token,
        "brand": "VISA",
        "last4": last4,
        "exp_month": 12,
        "exp_year": now.year + 2,
        "is_default": make_default,
        "status": "active",
    }
    created = client.table("payment_methods").insert(payload).execute()
    if not created.data:
        raise ValueError("Failed to add payment method")

    row = created.data[0]
    return {
        "payment_method_id": row["id"],
        "brand": row.get("brand"),
        "last4": row.get("last4"),
        "exp_month": row.get("exp_month"),
        "exp_year": row.get("exp_year"),
        "is_default": bool(row.get("is_default", False)),
        "status": row.get("status", "active"),
    }


async def list_invoices(
    client: Client,
    *,
    account_id: str,
    limit: int,
    cursor: str | None,
) -> dict[str, Any]:
    query = (
        client.table("invoices")
        .select("*")
        .eq("account_id", account_id)
        .order("id", desc=False)
    )
    if cursor:
        query = query.gt("id", _decode_cursor(cursor))

    rows = query.limit(limit + 1).execute().data or []
    has_more = len(rows) > limit
    page_rows = rows[:limit]
    next_cursor = _encode_cursor(page_rows[-1]["id"]) if has_more and page_rows else None

    items = [
        {
            "invoice_id": row["id"],
            "invoice_number": row.get("invoice_number"),
            "status": row.get("status", "active"),
            "currency": row.get("currency", "USD"),
            "amount_total": float(row.get("amount_total") or 0),
            "period_start": row.get("period_start"),
            "period_end": row.get("period_end"),
            "issued_at": row.get("issued_at"),
            "paid_at": row.get("paid_at"),
        }
        for row in page_rows
    ]

    return {"items": items, "next_cursor": next_cursor, "has_more": has_more}


async def get_invoice_download(client: Client, *, account_id: str, invoice_id: str) -> dict[str, Any] | None:
    response = (
        client.table("invoices")
        .select("pdf_url")
        .eq("account_id", account_id)
        .eq("id", invoice_id)
        .limit(1)
        .execute()
    )
    if not response.data:
        return None

    pdf_url = response.data[0].get("pdf_url")
    if not pdf_url:
        return None

    return {
        "url": pdf_url,
        "expires_at": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
    }
