from enum import Enum

from pydantic import BaseModel


class ChannelStatus(str, Enum):
    NORMAL = "normal"
    VERIFIED = "verified"
    SCAM = "scam"
    RESTRICTED = "restricted"
    DELETED = "deleted"


class ChannelSizeBucket(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    HUGE = "huge"


class ChannelSortBy(str, Enum):
    SUBSCRIBERS = "subscribers"
    GROWTH_24H = "growth_24h"
    GROWTH_7D = "growth_7d"
    GROWTH_30D = "growth_30d"
    ENGAGEMENT_RATE = "engagement_rate"
    UPDATED_AT = "updated_at"


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class ChannelListItem(BaseModel):
    channel_id: str
    name: str
    username: str | None = None
    subscribers: int
    growth_24h: float | None = None
    growth_7d: float | None = None
    growth_30d: float | None = None
    engagement_rate: float | None = None
    category_slug: str | None = None
    category_name: str | None = None
    country_code: str | None = None
    status: ChannelStatus
    verified: bool
    scam: bool


class PageResponse(BaseModel):
    next_cursor: str | None
    has_more: bool


class ChannelListMeta(BaseModel):
    total_estimate: int


class ChannelListEnvelope(BaseModel):
    data: list[ChannelListItem]
    page: PageResponse
    meta: ChannelListMeta
