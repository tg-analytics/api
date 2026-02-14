from enum import Enum

from pydantic import BaseModel, Field


class MiniAppsPeriod(str, Enum):
    D7 = "7d"
    D30 = "30d"


class MiniAppSortBy(str, Enum):
    DAILY_USERS = "daily_users"
    GROWTH = "growth"
    RATING = "rating"
    LAUNCHED_AT = "launched_at"


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class MiniAppListItem(BaseModel):
    mini_app_id: str
    name: str
    slug: str
    category_slug: str | None = None
    daily_users: int | None = None
    total_users: int | None = None
    sessions: int | None = None
    rating: float | None = None
    growth_weekly: float | None = None
    launched_at: str | None = None


class PageResponse(BaseModel):
    next_cursor: str | None
    has_more: bool


class MiniAppListMeta(BaseModel):
    total_estimate: int


class MiniAppListEnvelope(BaseModel):
    data: list[MiniAppListItem]
    page: PageResponse
    meta: MiniAppListMeta


class MiniAppsSummary(BaseModel):
    total_mini_apps: int
    daily_active_users: int
    total_sessions: int
    avg_session_seconds: int
    total_mini_apps_delta: int | None = None
    daily_active_users_delta: int | None = None
    daily_active_users_delta_percent: float | None = None
    total_sessions_delta: int | None = None
    total_sessions_delta_percent: float | None = None
    avg_session_seconds_delta: int | None = None


class MiniAppsSummaryEnvelope(BaseModel):
    data: MiniAppsSummary
    meta: dict[str, object] = Field(default_factory=dict)
