from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True


class UserMeResponse(BaseModel):
    """Response schema for /users/me endpoint"""
    email: str
    first_name: str | None = None
    last_name: str | None = None
    default_account_id: str | None = None