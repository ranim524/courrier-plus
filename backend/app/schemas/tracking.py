from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import ActorType, LetterEventType, LetterStatus
from app.schemas.delivery import DeliveryPublicView


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
    delivery: DeliveryPublicView | None = None
