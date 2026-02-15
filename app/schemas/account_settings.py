from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class PageResponse(BaseModel):
    next_cursor: str | None
    has_more: bool


class MeProfile(BaseModel):
    user_id: str
    first_name: str | None = None
    last_name: str | None = None
    full_name: str | None = None
    email: str | None = None
    telegram_username: str | None = None
    avatar_url: str | None = None


class MeUpdateRequest(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    telegram_username: str | None = Field(default=None, min_length=2, max_length=64)
    avatar_url: str | None = Field(default=None, min_length=1, max_length=2048)

    @field_validator("first_name", "last_name", "telegram_username", "avatar_url")
    @classmethod
    def strip_non_empty(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class UserPreferences(BaseModel):
    language_code: str
    timezone: str
    theme: str


class UserPreferencesUpdateRequest(BaseModel):
    language_code: str | None = None
    timezone: str | None = None
    theme: str | None = None

    @field_validator("language_code", "timezone", "theme")
    @classmethod
    def strip_values(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @model_validator(mode="after")
    def at_least_one_field(self) -> "UserPreferencesUpdateRequest":
        if self.language_code is None and self.timezone is None and self.theme is None:
            raise ValueError("At least one field must be provided")
        return self


class NotificationSettings(BaseModel):
    email_notifications: bool
    telegram_bot_alerts: bool
    weekly_reports: bool
    marketing_updates: bool
    push_notifications: bool


class NotificationSettingsUpdateRequest(BaseModel):
    email_notifications: bool | None = None
    telegram_bot_alerts: bool | None = None
    weekly_reports: bool | None = None
    marketing_updates: bool | None = None
    push_notifications: bool | None = None

    @model_validator(mode="after")
    def at_least_one_field(self) -> "NotificationSettingsUpdateRequest":
        if (
            self.email_notifications is None
            and self.telegram_bot_alerts is None
            and self.weekly_reports is None
            and self.marketing_updates is None
            and self.push_notifications is None
        ):
            raise ValueError("At least one field must be provided")
        return self


class MeEnvelope(BaseModel):
    data: MeProfile
    meta: dict[str, object] = Field(default_factory=dict)


class UserPreferencesEnvelope(BaseModel):
    data: UserPreferences
    meta: dict[str, object] = Field(default_factory=dict)


class NotificationSettingsEnvelope(BaseModel):
    data: NotificationSettings
    meta: dict[str, object] = Field(default_factory=dict)


class AccountChannel(BaseModel):
    account_id: str
    channel_id: str
    alias_name: str | None = None
    monitoring_enabled: bool
    is_favorite: bool
    added_at: datetime


class AddAccountChannelRequest(BaseModel):
    telegram_channel_id: int = Field(gt=0)
    channel_name: str = Field(min_length=1, max_length=255)
    alias_name: str | None = None
    monitoring_enabled: bool = True
    is_favorite: bool = False

    @field_validator("channel_name")
    @classmethod
    def strip_channel_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class AccountChannelInsights(BaseModel):
    total_subscribers: int
    total_views: int
    avg_engagement_rate: float
    channels_count: int


class VerificationRequest(BaseModel):
    request_id: str
    account_id: str
    channel_id: str
    verification_code: str
    verification_method: str
    status: str
    requested_at: datetime
    confirmed_at: datetime | None = None
    expires_at: datetime


class VerificationRequestCreateRequest(BaseModel):
    verification_method: str = "description_code"


class VerificationConfirmRequest(BaseModel):
    evidence: dict[str, object] = Field(default_factory=dict)


class AccountChannelEnvelope(BaseModel):
    data: AccountChannel
    meta: dict[str, object] = Field(default_factory=dict)


class AccountChannelListEnvelope(BaseModel):
    data: list[AccountChannel]
    page: PageResponse
    meta: dict[str, object] = Field(default_factory=dict)


class AccountChannelInsightsEnvelope(BaseModel):
    data: AccountChannelInsights
    meta: dict[str, object] = Field(default_factory=dict)


class VerificationRequestEnvelope(BaseModel):
    data: VerificationRequest
    meta: dict[str, object] = Field(default_factory=dict)


class ApiKeyListItem(BaseModel):
    api_key_id: str
    name: str
    key_prefix: str
    scopes: list[str]
    rate_limit_per_hour: int
    created_at: datetime
    last_used_at: datetime | None = None
    revoked_at: datetime | None = None


class ApiKeyCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    scopes: list[str] = Field(default_factory=lambda: ["read"])
    rate_limit_per_hour: int = Field(default=1000, ge=1)


class ApiKeyCreateResponse(BaseModel):
    api_key: ApiKeyListItem
    secret: str


class ApiUsageByDay(BaseModel):
    date: date
    requests: int
    errors: int


class ApiUsage(BaseModel):
    total_requests: int
    error_rate: float
    avg_latency_ms: float
    by_day: list[ApiUsageByDay]


class ApiKeyListEnvelope(BaseModel):
    data: list[ApiKeyListItem]
    meta: dict[str, object] = Field(default_factory=dict)


class ApiKeyCreateEnvelope(BaseModel):
    data: ApiKeyCreateResponse
    meta: dict[str, object] = Field(default_factory=dict)


class ApiUsageEnvelope(BaseModel):
    data: ApiUsage
    meta: dict[str, object] = Field(default_factory=dict)


class Subscription(BaseModel):
    subscription_id: str
    account_id: str
    plan_code: str
    status: str
    billing_state: str
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    cancel_at_period_end: bool


class SubscriptionUpdateRequest(BaseModel):
    plan_code: str | None = None
    cancel_at_period_end: bool | None = None

    @model_validator(mode="after")
    def at_least_one_field(self) -> "SubscriptionUpdateRequest":
        if self.plan_code is None and self.cancel_at_period_end is None:
            raise ValueError("At least one field must be provided")
        return self


class AccountUsage(BaseModel):
    from_date: date = Field(alias="from")
    to_date: date = Field(alias="to")
    channel_searches: int
    event_trackers_count: int
    api_requests_count: int
    exports_count: int


class PaymentMethod(BaseModel):
    payment_method_id: str
    brand: str | None = None
    last4: str | None = None
    exp_month: int | None = None
    exp_year: int | None = None
    is_default: bool
    status: str


class PaymentMethodCreateRequest(BaseModel):
    provider_payment_method_token: str = Field(min_length=1)
    make_default: bool = True


class Invoice(BaseModel):
    invoice_id: str
    invoice_number: str | None = None
    status: str
    currency: str
    amount_total: float
    period_start: date | None = None
    period_end: date | None = None
    issued_at: datetime | None = None
    paid_at: datetime | None = None


class InvoiceDownload(BaseModel):
    url: str
    expires_at: datetime


class SubscriptionEnvelope(BaseModel):
    data: Subscription
    meta: dict[str, object] = Field(default_factory=dict)


class AccountUsageEnvelope(BaseModel):
    data: AccountUsage
    meta: dict[str, object] = Field(default_factory=dict)


class PaymentMethodEnvelope(BaseModel):
    data: PaymentMethod
    meta: dict[str, object] = Field(default_factory=dict)


class PaymentMethodListEnvelope(BaseModel):
    data: list[PaymentMethod]
    meta: dict[str, object] = Field(default_factory=dict)


class InvoiceListEnvelope(BaseModel):
    data: list[Invoice]
    page: PageResponse
    meta: dict[str, object] = Field(default_factory=dict)


class InvoiceDownloadEnvelope(BaseModel):
    data: InvoiceDownload
    meta: dict[str, object] = Field(default_factory=dict)
