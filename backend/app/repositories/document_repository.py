from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document


def create(db: Session, document: Document) -> Document:
    db.add(document)
    db.flush()
    return document


def get_by_letter_id(db: Session, letter_id: UUID) -> Document | None:
    stmt = select(Document).where(Document.letter_id == letter_id)
    return db.execute(stmt).scalar_one_or_none()
