from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import ActorType, EmailStatus, EmailType, LetterEventType


class LetterEventRead(BaseModel):
    id: UUID
    event_type: LetterEventType
    actor_type: ActorType
    ip_address: str | None
    user_agent: str | None
    event_metadata: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class EmailEventRead(BaseModel):
    id: UUID
    email_type: EmailType
    recipient: str
    status: EmailStatus
    provider_message_id: str | None
    error_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
