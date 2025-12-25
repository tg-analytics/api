from datetime import datetime

from pydantic import BaseModel, EmailStr


class MagicLinkRequest(BaseModel):
    email: EmailStr


class MagicLinkResponse(BaseModel):
    token: str
    expires_at: datetime


class MagicLinkConfirmRequest(BaseModel):
    email: EmailStr
    token: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str | None
    role: str
    status: str
    is_guest: bool


class MagicLinkConfirmResponse(BaseModel):
    access_token: str
    token_type: str
    expires_at: datetime
    user: UserResponse