from pydantic import BaseModel


class RankingChannelItem(BaseModel):
    rank: int
    channel_id: str
    name: str
    username: str | None = None
    subscribers: int | None = None
    growth_7d: float | None = None
    engagement_rate: float | None = None


class CountryRankingItem(RankingChannelItem):
    context_type: str = "country"
    context_label: str
    trend_label: str = "growth_7d"
    trend_value: float | None = None


class CategoryRankingItem(RankingChannelItem):
    context_type: str = "category"
    context_label: str
    trend_label: str = "engagement_rate"
    trend_value: float | None = None


class RankingCollectionItem(BaseModel):
    collection_id: str
    slug: str
    name: str
    description: str | None = None
    icon: str | None = None
    channels_count: int
    cta_label: str = "Explore"
    cta_target: str


class CountryRankingsMeta(BaseModel):
    country_code: str
    country_name: str | None = None
    snapshot_date: str | None = None
    total_ranked_channels: int
    applied_limit: int


class CategoryRankingsMeta(BaseModel):
    category_slug: str
    category_name: str | None = None
    snapshot_date: str | None = None
    total_ranked_channels: int
    applied_limit: int


class RankingCollectionsMeta(BaseModel):
    total_active_collections: int
    applied_limit: int


class CountryRankingsEnvelope(BaseModel):
    data: list[CountryRankingItem]
    meta: CountryRankingsMeta


class CategoryRankingsEnvelope(BaseModel):
    data: list[CategoryRankingItem]
    meta: CategoryRankingsMeta


class RankingCollectionsEnvelope(BaseModel):
    data: list[RankingCollectionItem]
    meta: RankingCollectionsMeta
