from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import get_settings

settings = get_settings()


def _create_engine(database_url: str):
    parsed_url = make_url(database_url)

    if parsed_url.drivername in {"http", "https"}:
        raise ValueError(
            "DATABASE_URL looks like an HTTP(S) URL. "
            "Use a database connection string instead (for Supabase, copy the "
            "Postgres connection string from Settings → Database, e.g. "
            "'postgresql+asyncpg://postgres:<password>@db.<project>.supabase.co:5432/postgres'). "
            "Other examples: 'postgresql+asyncpg://user:password@host:5432/dbname' or "
            "'sqlite+aiosqlite:///./db.sqlite3'."
        )

    return create_async_engine(database_url, echo=False, future=True)


engine = _create_engine(settings.database_url)

AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

Base = declarative_base()


async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
