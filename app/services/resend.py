from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from app.core.config import get_settings

RESEND_EMAILS_URL = "https://api.resend.com/emails"


class ResendError(Exception):
    """Base exception for Resend adapter errors."""


class ResendConfigurationError(ResendError):
    """Raised when required Resend configuration is missing."""


class ResendSendError(ResendError):
    """Raised when the Resend API responds with an error."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def _build_magic_link(token: str, base_url: str | None) -> str:
    if not base_url:
        return token

    if "{token}" in base_url:
        return base_url.format(token=token)

    separator = "&" if "?" in base_url else "?"
    return f"{base_url.rstrip('/')}{separator}token={token}"


async def send_magic_link_email(*, recipient: str, token: str, expires_at: datetime) -> None:
    settings = get_settings()

    if not settings.resend_api_key:
        raise ResendConfigurationError("RESEND_API_KEY is not configured.")

    if not settings.resend_from_email:
        raise ResendConfigurationError("RESEND_FROM_EMAIL is not configured.")

    magic_link = _build_magic_link(token, settings.magic_link_base_url)
    subject = f"Your sign-in link for {settings.app_name}"

    text_body = "\n".join(
        [
            f"Use the magic link below to sign in to {settings.app_name}:",
            magic_link,
            "",
            f"This link expires at {expires_at.isoformat()}.",
            "",
            "If you did not request this email, you can safely ignore it.",
        ]
    )

    html_body = (
        f"<p>Use the magic link below to sign in to {settings.app_name}:</p>"
        f'<p><a href="{magic_link}">{magic_link}</a></p>'
        f"<p>This link expires at {expires_at.isoformat()}.</p>"
        "<p>If you did not request this email, you can safely ignore it.</p>"
    )

    payload: dict[str, Any] = {
        "from": str(settings.resend_from_email),
        "to": [recipient],
        "subject": subject,
        "text": text_body,
        "html": html_body,
    }

    headers = {"Authorization": f"Bearer {settings.resend_api_key}"}

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(RESEND_EMAILS_URL, json=payload, headers=headers)

    if not response.is_success:
        error_message = "Resend email send failed."

        try:
            data = response.json()
            if isinstance(data, dict) and data.get("message"):
                error_message = str(data["message"])
        except ValueError:
            pass

        raise ResendSendError(error_message, status_code=response.status_code)


async def send_welcome_email(*, recipient: str, first_name: str | None = None) -> None:
    """Send a welcome email to a new user."""
    settings = get_settings()

    if not settings.resend_api_key:
        raise ResendConfigurationError("RESEND_API_KEY is not configured.")

    if not settings.resend_from_email:
        raise ResendConfigurationError("RESEND_FROM_EMAIL is not configured.")

    greeting_name = first_name or recipient.split("@")[0]
    subject = f"Welcome to {settings.app_name}!"

    text_body = "\n".join(
        [
            f"Hi {greeting_name},",
            "",
            f"Welcome to {settings.app_name}! We're excited to have you on board.",
            "You can sign in anytime using your email and magic link.",
            "",
            "If you have any questions, just reply to this email.",
        ]
    )

    html_body = (
        f"<p>Hi {greeting_name},</p>"
        f"<p>Welcome to <strong>{settings.app_name}</strong>! We're excited to have you on board.</p>"
        "<p>You can sign in anytime using your email and magic link.</p>"
        "<p>If you have any questions, just reply to this email.</p>"
    )

    payload: dict[str, Any] = {
        "from": str(settings.resend_from_email),
        "to": [recipient],
        "subject": subject,
        "text": text_body,
        "html": html_body,
    }

    headers = {"Authorization": f"Bearer {settings.resend_api_key}"}

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(RESEND_EMAILS_URL, json=payload, headers=headers)

    if not response.is_success:
        error_message = "Resend email send failed."

        try:
            data = response.json()
            if isinstance(data, dict) and data.get("message"):
                error_message = str(data["message"])
        except ValueError:
            pass

        raise ResendSendError(error_message, status_code=response.status_code)
