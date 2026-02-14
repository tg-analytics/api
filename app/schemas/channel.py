from enum import Enum

from pydantic import BaseModel, Field


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


class ChannelOverviewChannel(BaseModel):
    channel_id: str
    telegram_channel_id: int
    name: str
    username: str | None = None
    avatar_url: str | None = None
    description: str | None = None
    about_text: str | None = None
    website_url: str | None = None
    status: ChannelStatus
    country_code: str | None = None
    category_slug: str | None = None
    category_name: str | None = None


class ChannelOverviewKpi(BaseModel):
    value: int | float | None = None
    delta: int | float | None = None
    delta_percent: float | None = None


class ChannelOverviewKpis(BaseModel):
    subscribers: ChannelOverviewKpi
    avg_views: ChannelOverviewKpi
    engagement_rate: ChannelOverviewKpi
    posts_per_day: ChannelOverviewKpi


class ChannelOverviewChartPoint(BaseModel):
    date: str
    subscribers: int | None = None
    engagement_rate: float | None = None


class ChannelOverviewChart(BaseModel):
    range: str
    points: list[ChannelOverviewChartPoint]


class ChannelOverviewSimilarChannel(BaseModel):
    channel_id: str
    name: str
    username: str | None = None
    subscribers: int | None = None
    similarity_score: float


class ChannelOverviewTag(BaseModel):
    tag_id: str
    slug: str
    name: str
    relevance_score: float | None = None


class ChannelOverviewInOut(BaseModel):
    incoming: int
    outgoing: int


class ChannelOverviewPost(BaseModel):
    post_id: str
    telegram_message_id: int
    published_at: str
    title: str | None = None
    content_text: str | None = None
    views_count: int
    reactions_count: int
    comments_count: int
    forwards_count: int
    external_post_url: str | None = None


class ChannelOverviewData(BaseModel):
    channel: ChannelOverviewChannel
    kpis: ChannelOverviewKpis
    chart: ChannelOverviewChart
    similar_channels: list[ChannelOverviewSimilarChannel]
    tags: list[ChannelOverviewTag]
    recent_posts: list[ChannelOverviewPost]
    inout_30d: ChannelOverviewInOut
    incoming_30d: int
    outgoing_30d: int


class ChannelOverviewEnvelope(BaseModel):
    data: ChannelOverviewData
    meta: dict[str, object] = Field(default_factory=dict)
