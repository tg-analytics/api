from functools import lru_cache
from urllib.parse import quote_plus, urlparse

from pydantic import EmailStr, model_validator
from pydantic.version import VERSION

if VERSION.startswith("1."):
    raise ImportError(
        f"Pydantic v2+ is required (found v{VERSION}). Reinstall dependencies with ``pip install -r requirements.txt``."
    )

from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "fastapi-starter-kit"
    database_url: str | None = None
    supabase_url: str | None = None
    supabase_service_key: str | None = None
    supabase_db_password: str | None = None
    secret_key: str = "change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    resend_api_key: str | None = None
    resend_from_email: EmailStr | None = None
    magic_link_base_url: str | None = None

    @model_validator(mode="after")
    def build_database_url(self):
        if self.database_url:
            supabase_host = self._parse_supabase_host(self.database_url, allow_supabase_only=True)

            if supabase_host:
                self.database_url = self._build_supabase_database_url(supabase_host)
            else:
                self._validate_database_url(self.database_url)

            return self

        if self.supabase_url:
            supabase_host = self._parse_supabase_host(self.supabase_url)
            if not supabase_host:
                raise ValueError(
                    "SUPABASE_URL must be a valid Supabase project URL (e.g. https://<project>.supabase.co)."
                )

            self.database_url = self._build_supabase_database_url(supabase_host)
        else:
            self.database_url = DEFAULT_DATABASE_URL

        return self

    def _parse_supabase_host(self, url: str, allow_supabase_only: bool = False) -> str | None:
        parsed = urlparse(url)

        if parsed.scheme in {"http", "https"}:
            if parsed.hostname and parsed.hostname.endswith(".supabase.co"):
                return parsed.hostname

            if allow_supabase_only:
                raise ValueError(
                    "DATABASE_URL looks like an HTTP(S) URL. For Supabase, set SUPABASE_URL to your project URL "
                    "(e.g. https://<project>.supabase.co) and provide SUPABASE_DB_PASSWORD or SUPABASE_SERVICE_KEY. "
                    "Otherwise use a Postgres connection string such as "
                    "'postgresql+asyncpg://user:password@host:5432/dbname' or 'sqlite+aiosqlite:///./db.sqlite3'."
                )

        if not parsed.scheme and allow_supabase_only:
            raise ValueError("DATABASE_URL is missing a scheme. Provide a full database connection string.")

        return None

    def _build_supabase_database_url(self, supabase_host: str) -> str:
        db_host = supabase_host if supabase_host.startswith("db.") else f"db.{supabase_host}"
        password = self.supabase_db_password or self.supabase_service_key

        if not password:
            raise ValueError(
                "SUPABASE_URL was provided but no password was found. "
                "Set SUPABASE_DB_PASSWORD from Supabase → Settings → Database (Connection string) "
                "or supply SUPABASE_SERVICE_KEY if you intend to use it for the database connection."
            )

        return f"postgresql+asyncpg://postgres:{quote_plus(password)}@{db_host}:5432/postgres"

    def _validate_database_url(self, database_url: str) -> None:
        parsed_scheme = urlparse(database_url).scheme

        if parsed_scheme in {"http", "https"}:
            raise ValueError(
                "DATABASE_URL looks like an HTTP(S) URL. For Supabase, set SUPABASE_URL and "
                "SUPABASE_DB_PASSWORD (or SUPABASE_SERVICE_KEY). Otherwise, provide a Postgres connection string."
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()
