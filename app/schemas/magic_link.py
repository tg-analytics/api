from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class MagicLinkRequest(BaseModel):
    email: EmailStr


class MagicLinkResponse(BaseModel):
    token: str
    expires_at: datetime


class MagicLinkConfirm(BaseModel):
    email: EmailStr
    token: str


class GoogleSigninRequest(BaseModel):
    id_token: str
    account_id: UUID | None = None
