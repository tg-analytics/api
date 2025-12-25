from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.magic_token import create_magic_token
from app.crud.user import get_user_by_email
from app.db.base import get_session
from app.services.resend import ResendConfigurationError, ResendSendError, send_magic_link_email
from app.schemas.magic_link import MagicLinkRequest, MagicLinkResponse

MAGIC_LINK_EXPIRY_MINUTES = 15

router = APIRouter(prefix="/v1.0", tags=["signin"])


@router.post("/signin", response_model=MagicLinkResponse, status_code=status.HTTP_201_CREATED)
async def create_magic_link(
    payload: MagicLinkRequest, session: AsyncSession = Depends(get_session)
) -> MagicLinkResponse:
    user = await get_user_by_email(session, payload.email)

    token = str(uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=MAGIC_LINK_EXPIRY_MINUTES)

    await create_magic_token(
        session,
        email=payload.email,
        token=token,
        expires_at=expires_at,
        user_id=user.id if user else None,
    )

    try:
        await send_magic_link_email(recipient=payload.email, token=token, expires_at=expires_at)
    except ResendConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except ResendSendError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return MagicLinkResponse(token=token, expires_at=expires_at)
