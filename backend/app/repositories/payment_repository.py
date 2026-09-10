from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.payment import Payment


def create(db: Session, payment: Payment) -> Payment:
    db.add(payment)
    db.flush()
    return payment


def get_by_transaction_id(db: Session, transaction_id: str) -> Payment | None:
    stmt = select(Payment).where(Payment.transaction_id == transaction_id)
    return db.execute(stmt).scalar_one_or_none()


def get_by_letter_id(db: Session, letter_id: UUID) -> Payment | None:
    stmt = select(Payment).where(Payment.letter_id == letter_id).order_by(Payment.created_at.desc())
    return db.execute(stmt).scalars().first()


def list_payments(db: Session, page: int, page_size: int) -> tuple[list[Payment], int]:
    total = db.execute(select(func.count(Payment.id))).scalar_one()
    stmt = (
        select(Payment)
        .order_by(Payment.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = list(db.execute(stmt).scalars().all())
    return items, total


def sum_paid_amount(db: Session) -> float:
    from app.models.enums import PaymentStatus

    stmt = select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.status == PaymentStatus.PAID)
    return float(db.execute(stmt).scalar_one())


def count_all(db: Session) -> int:
    return db.execute(select(func.count(Payment.id))).scalar_one()
