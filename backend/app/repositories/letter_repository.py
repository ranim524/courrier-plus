from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.enums import LetterStatus
from app.models.letter import Letter


def create(db: Session, letter: Letter) -> Letter:
    db.add(letter)
    db.flush()
    return letter


def get_by_id(db: Session, letter_id: UUID) -> Letter | None:
    return db.get(Letter, letter_id)


def get_by_id_with_document(db: Session, letter_id: UUID) -> Letter | None:
    stmt = select(Letter).options(joinedload(Letter.document)).where(Letter.id == letter_id)
    return db.execute(stmt).unique().scalar_one_or_none()


def get_by_reference(db: Session, reference: str) -> Letter | None:
    stmt = select(Letter).where(Letter.reference == reference)
    return db.execute(stmt).scalar_one_or_none()


def reference_exists(db: Session, reference: str) -> bool:
    stmt = select(Letter.id).where(Letter.reference == reference)
    return db.execute(stmt).first() is not None


def list_letters(
    db: Session,
    page: int,
    page_size: int,
    status: LetterStatus | None = None,
    search: str | None = None,
) -> tuple[list[Letter], int]:
    stmt = select(Letter)
    count_stmt = select(func.count(Letter.id))

    if status is not None:
        stmt = stmt.where(Letter.status == status)
        count_stmt = count_stmt.where(Letter.status == status)

    if search:
        pattern = f"%{search}%"
        condition = or_(
            Letter.reference.ilike(pattern),
            Letter.sender_first_name.ilike(pattern),
            Letter.sender_last_name.ilike(pattern),
            Letter.sender_email.ilike(pattern),
            Letter.recipient_first_name.ilike(pattern),
            Letter.recipient_last_name.ilike(pattern),
            Letter.recipient_email.ilike(pattern),
        )
        stmt = stmt.where(condition)
        count_stmt = count_stmt.where(condition)

    total = db.execute(count_stmt).scalar_one()

    stmt = stmt.order_by(Letter.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    items = list(db.execute(stmt).scalars().all())

    return items, total


def count_by_status(db: Session, status: LetterStatus) -> int:
    stmt = select(func.count(Letter.id)).where(Letter.status == status)
    return db.execute(stmt).scalar_one()


def count_all(db: Session) -> int:
    return db.execute(select(func.count(Letter.id))).scalar_one()
