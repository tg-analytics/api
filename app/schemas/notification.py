from datetime import datetime

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    """Response schema for user notifications."""
    id: str
    user_id: str
    subject: str
    body: str
    is_read: bool
    read_at: datetime | None
    created_at: datetime
