from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator


class TeamMemberInvite(BaseModel):
    """Request schema for inviting a team member"""
    email: EmailStr
    role: str

    @field_validator("role")
    @classmethod
    def disallow_owner_role(cls, value: str) -> str:
        """Prevent inviting team members with the owner role."""
        if value.lower() == "owner":
            raise ValueError("Inviting a team member with the owner role is not allowed")
        return value


class TeamMemberResponse(BaseModel):
    """Response schema for team member details"""
    id: str
    role: str
    user_id: str
    name: str | None
    joined_at: datetime


class TeamMemberUpdate(BaseModel):
    """Request schema for updating a team member"""
    role: str | None = None
