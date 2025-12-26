from datetime import datetime
from pydantic import BaseModel, EmailStr


class TeamMemberInvite(BaseModel):
    """Request schema for inviting a team member"""
    email: EmailStr
    role: str


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
