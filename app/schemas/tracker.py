from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


class TrackerType(str, Enum):
    KEYWORD = "keyword"
    CHANNEL = "channel"


class TrackerStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class PageResponse(BaseModel):
    next_cursor: str | None
    has_more: bool


class Tracker(BaseModel):
    tracker_id: str
    account_id: str
    tracker_type: TrackerType
    tracker_value: str
    status: TrackerStatus
    mentions_count: int
    last_activity_at: datetime | None = None
    notify_push: bool
    notify_telegram: bool
    notify_email: bool


class TrackerCreateRequest(BaseModel):
    tracker_type: TrackerType
    tracker_value: str
    notify_push: bool = True
    notify_telegram: bool = True
    notify_email: bool = False

    @field_validator("tracker_value")
    @classmethod
    def validate_tracker_value(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("tracker_value must not be empty")
        return normalized


class TrackerUpdateRequest(BaseModel):
    status: TrackerStatus | None = None
    notify_push: bool | None = None
    notify_telegram: bool | None = None
    notify_email: bool | None = None

    @model_validator(mode="after")
    def validate_at_least_one_field(self) -> "TrackerUpdateRequest":
        if (
            self.status is None
            and self.notify_push is None
            and self.notify_telegram is None
            and self.notify_email is None
        ):
            raise ValueError("At least one field must be provided for update")
        return self


class TrackerMention(BaseModel):
    mention_id: str
    tracker_id: str
    mention_seq: int
    channel_id: str | None = None
    channel_name: str | None = None
    post_id: str | None = None
    mention_text: str
    context_snippet: str | None = None
    mentioned_at: datetime


class TrackerEnvelope(BaseModel):
    data: Tracker
    meta: dict[str, object] = Field(default_factory=dict)


class TrackerListEnvelope(BaseModel):
    data: list[Tracker]
    meta: dict[str, object] = Field(default_factory=dict)


class TrackerMentionListEnvelope(BaseModel):
    data: list[TrackerMention]
    page: PageResponse
    meta: dict[str, object] = Field(default_factory=dict)
