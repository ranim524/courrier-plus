from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.email_event import EmailEvent


def create(db: Session, event: EmailEvent) -> EmailEvent:
    db.add(event)
    db.flush()
    return event


def list_for_letter(db: Session, letter_id: UUID) -> list[EmailEvent]:
    stmt = select(EmailEvent).where(EmailEvent.letter_id == letter_id).order_by(EmailEvent.created_at)
    return list(db.execute(stmt).scalars().all())


def list_all(db: Session, page: int, page_size: int) -> tuple[list[EmailEvent], int]:
    total = db.execute(select(func.count(EmailEvent.id))).scalar_one()
    stmt = (
        select(EmailEvent)
        .order_by(EmailEvent.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = list(db.execute(stmt).scalars().all())
    return items, total
