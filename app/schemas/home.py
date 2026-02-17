from pydantic import BaseModel


class HomeCategoryItem(BaseModel):
    slug: str
    name: str
    icon: str | None = None
    channels_count: int


class PageResponse(BaseModel):
    next_cursor: str | None
    has_more: bool


class HomeCategoriesMeta(BaseModel):
    total_estimate: int


class HomeCategoriesEnvelope(BaseModel):
    data: list[HomeCategoryItem]
    page: PageResponse
    meta: HomeCategoriesMeta


class HomeCountryItem(BaseModel):
    code: str
    name: str
    flag_emoji: str | None = None
    channels_count: int


class HomeCountriesMeta(BaseModel):
    total_estimate: int


class HomeCountriesEnvelope(BaseModel):
    data: list[HomeCountryItem]
    page: PageResponse
    meta: HomeCountriesMeta
