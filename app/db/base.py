from functools import lru_cache
from typing import AsyncGenerator, Generator

import httpx
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from supabase import Client, ClientOptions, create_client

from ..core.config import get_settings

Base = declarative_base()

_supabase_client: Client | None = None


@lru_cache
def get_engine():
    settings = get_settings()
    return create_async_engine(settings.database_url, future=True)


@lru_cache
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=get_engine(), expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields an async database session."""

    session_factory = get_sessionmaker()
    async with session_factory() as session:
        yield session


def _initialize_client() -> Client:
    settings = get_settings()
    client_options = ClientOptions()

    if settings.supabase_proxy:
        http_client = httpx.Client(proxy=settings.supabase_proxy)
        client_options.httpx_client = http_client

    return create_client(
        settings.supabase_url,
        settings.supabase_service_key,
        options=client_options,
    )


def get_supabase_client() -> Generator[Client, None, None]:
    """Dependency that yields a Supabase client instance."""

    global _supabase_client
    if _supabase_client is None:
        _supabase_client = _initialize_client()
    yield _supabase_client


def verify_epictwin_connection(client: Client) -> dict:
    """Run a lightweight query against the epictwin table to confirm connectivity."""

    response = client.table("epictwin").select("*").limit(1).execute()
    return {
        "table": "epictwin",
        "row_count": len(response.data or []),
    }
