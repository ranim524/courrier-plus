from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import ActorType, LetterEventType, LetterStatus


class TrackingEvent(BaseModel):
    event_type: LetterEventType
    actor_type: ActorType
    created_at: datetime

    model_config = {"from_attributes": True}


class TrackingRead(BaseModel):
    reference: str
    status: LetterStatus
    subject: str
    sender_first_name: str
    sender_last_name: str
    recipient_first_name: str
    recipient_last_name: str
    created_at: datetime
    events: list[TrackingEvent]


class AccessLetterView(BaseModel):
    reference: str
    sender_first_name: str
    sender_last_name: str
    subject: str
    message: str | None
    status: LetterStatus
    has_document: bool
    acknowledgment_of_receipt: bool
    created_at: datetime
