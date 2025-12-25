from typing import Generator

import httpx
from supabase import Client, ClientOptions, create_client

from ..core.config import get_settings

_supabase_client: Client | None = None


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