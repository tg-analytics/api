from enum import Enum

from pydantic import BaseModel


class AdvertiserSortBy(str, Enum):
    ESTIMATED_SPEND = "estimated_spend"
    TOTAL_ADS = "total_ads"
    CHANNELS_USED = "channels_used"
    AVG_ENGAGEMENT_RATE = "avg_engagement_rate"
    TREND = "trend"


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class AdvertiserActivityStatus(str, Enum):
    ALL = "all"
    ACTIVE = "active"
    RECENT = "recent"


class AdvertiserTimePeriodDays(int, Enum):
    D7 = 7
    D30 = 30
    D90 = 90
    D365 = 365


class AdvertiserListItem(BaseModel):
    rank: int
    advertiser_id: str
    name: str
    slug: str
    logo_url: str | None = None
    industry_slug: str | None = None
    industry_name: str | None = None
    estimated_spend: float | None = None
    total_ads: int | None = None
    channels_used: int | None = None
    avg_engagement_rate: float | None = None
    trend: float | None = None
    active_creatives: int | None = None
    last_active_at: str | None = None


class AdvertiserTopChannel(BaseModel):
    channel_id: str
    name: str
    username: str | None = None
    rank: int
    impressions: int | None = None
    estimated_spend: float | None = None
    engagement_rate: float | None = None


class AdvertiserDetail(BaseModel):
    advertiser_id: str
    name: str
    slug: str
    logo_url: str | None = None
    industry_slug: str | None = None
    industry_name: str | None = None
    estimated_spend: float | None = None
    total_ads: int | None = None
    channels_used: int | None = None
    avg_engagement_rate: float | None = None
    trend: float | None = None
    active_creatives: int | None = None
    last_active_at: str | None = None
    website_url: str | None = None
    description: str | None = None
    top_channels: list[AdvertiserTopChannel]


class PageResponse(BaseModel):
    next_cursor: str | None
    has_more: bool


class AdvertiserListMeta(BaseModel):
    total_estimate: int
    time_period_days: int
    snapshot_date: str | None = None
    baseline_date: str | None = None


class AdvertiserSummaryMeta(BaseModel):
    time_period_days: int
    snapshot_date: str | None = None
    baseline_date: str | None = None


class AdvertiserDetailMeta(BaseModel):
    snapshot_date: str | None = None


class AdvertiserSummary(BaseModel):
    active_advertisers: int
    total_ad_spend: float
    ad_campaigns: int
    avg_engagement_rate: float
    active_advertisers_delta: int | None = None
    total_ad_spend_delta: float | None = None
    total_ad_spend_delta_percent: float | None = None
    ad_campaigns_delta: int | None = None
    ad_campaigns_delta_percent: float | None = None
    avg_engagement_rate_delta: float | None = None
    avg_engagement_rate_delta_percent: float | None = None


class AdvertiserListEnvelope(BaseModel):
    data: list[AdvertiserListItem]
    page: PageResponse
    meta: AdvertiserListMeta


class AdvertiserSummaryEnvelope(BaseModel):
    data: AdvertiserSummary
    meta: AdvertiserSummaryMeta


class AdvertiserDetailEnvelope(BaseModel):
    data: AdvertiserDetail
    meta: AdvertiserDetailMeta
