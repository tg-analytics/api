from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.magic_token import MagicToken


async def create_magic_token(
    session: AsyncSession,
    *,
    email: str,
    token: str,
    expires_at: datetime,
    user_id: int | None = None,
) -> MagicToken:
    magic_token = MagicToken(
        email=email,
        token=token,
        expires_at=expires_at,
        user_id=user_id,
    )
    session.add(magic_token)
    await session.commit()
    await session.refresh(magic_token)
    return magic_token


async def get_magic_token_by_token(session: AsyncSession, token: str) -> MagicToken | None:
    result = await session.execute(select(MagicToken).where(MagicToken.token == token))
    return result.scalar_one_or_none()


async def get_magic_tokens_by_email(
    session: AsyncSession, email: str, *, active_only: bool = False
) -> list[MagicToken]:
    query = select(MagicToken).where(MagicToken.email == email)
    if active_only:
        now = datetime.now(timezone.utc)
        query = query.where(
            MagicToken.is_active.is_(True),
            MagicToken.consumed.is_(False),
            MagicToken.expires_at > now,
        )

    result = await session.execute(query.order_by(MagicToken.expires_at.desc()))
    return list(result.scalars().all())


async def mark_magic_token_consumed(session: AsyncSession, token: str) -> MagicToken | None:
    magic_token = await get_magic_token_by_token(session, token)
    if not magic_token:
        return None

    magic_token.consumed = True
    magic_token.is_active = False
    await session.commit()
    await session.refresh(magic_token)
    return magic_token


async def mark_magic_token_expired(session: AsyncSession, token: str) -> MagicToken | None:
    magic_token = await get_magic_token_by_token(session, token)
    if not magic_token:
        return None

    magic_token.is_active = False
    await session.commit()
    await session.refresh(magic_token)
    return magic_token
