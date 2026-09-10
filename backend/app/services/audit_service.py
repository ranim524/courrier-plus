from uuid import UUID

from sqlalchemy.orm import Session

from app.models.enums import ActorType, LetterEventType
from app.models.letter_event import LetterEvent
from app.repositories import letter_event_repository


def record_event(
    db: Session,
    letter_id: UUID,
    event_type: LetterEventType,
    actor_type: ActorType,
    ip_address: str | None = None,
    user_agent: str | None = None,
    metadata: dict | None = None,
) -> LetterEvent:
    event = LetterEvent(
        letter_id=letter_id,
        event_type=event_type,
        actor_type=actor_type,
        ip_address=ip_address,
        user_agent=user_agent,
        event_metadata=metadata,
    )
    return letter_event_repository.create(db, event)
