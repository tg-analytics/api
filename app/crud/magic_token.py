from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.magic_token import MagicToken


async def create_magic_token(
    session: AsyncSession,
    *,
    email: str,
    token: str,
    expires_at: datetime,
    user_id: int | None,
) -> MagicToken:
    magic_token = MagicToken(email=email, token=token, expires_at=expires_at, user_id=user_id)
    session.add(magic_token)
    await session.commit()
    await session.refresh(magic_token)
    return magic_token
