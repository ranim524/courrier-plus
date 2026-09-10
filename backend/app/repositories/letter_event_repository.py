from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.letter_event import LetterEvent


def create(db: Session, event: LetterEvent) -> LetterEvent:
    db.add(event)
    db.flush()
    return event


def list_for_letter(db: Session, letter_id: UUID) -> list[LetterEvent]:
    stmt = select(LetterEvent).where(LetterEvent.letter_id == letter_id).order_by(LetterEvent.created_at)
    return list(db.execute(stmt).scalars().all())
