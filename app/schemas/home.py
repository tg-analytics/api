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
