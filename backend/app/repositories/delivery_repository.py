from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.delivery import DeliveryAttempt, DeliveryOrder, ProofOfDelivery
from app.models.enums import DeliveryStatus


def create(db: Session, order: DeliveryOrder) -> DeliveryOrder:
    db.add(order)
    db.flush()
    return order


def tracking_number_exists(db: Session, tracking_number: str) -> bool:
    stmt = select(DeliveryOrder.id).where(DeliveryOrder.tracking_number == tracking_number)
    return db.execute(stmt).first() is not None


def get_by_id(db: Session, delivery_id: UUID) -> DeliveryOrder | None:
    stmt = (
        select(DeliveryOrder)
        .options(joinedload(DeliveryOrder.attempts), joinedload(DeliveryOrder.proof))
        .where(DeliveryOrder.id == delivery_id)
    )
    return db.execute(stmt).unique().scalar_one_or_none()


def get_by_letter_id(db: Session, letter_id: UUID) -> DeliveryOrder | None:
    stmt = select(DeliveryOrder).where(DeliveryOrder.letter_id == letter_id)
    return db.execute(stmt).scalar_one_or_none()


def get_by_tracking_number(db: Session, tracking_number: str) -> DeliveryOrder | None:
    stmt = select(DeliveryOrder).where(DeliveryOrder.tracking_number == tracking_number)
    return db.execute(stmt).scalar_one_or_none()


def list_deliveries(
    db: Session,
    page: int,
    page_size: int,
    status: DeliveryStatus | None = None,
    provider_id: UUID | None = None,
    courier_id: UUID | None = None,
    search: str | None = None,
) -> tuple[list[DeliveryOrder], int]:
    from app.models.letter import Letter

    stmt = select(DeliveryOrder)
    count_stmt = select(func.count(DeliveryOrder.id))

    if search:
        stmt = stmt.join(Letter, Letter.id == DeliveryOrder.letter_id)
        count_stmt = count_stmt.join(Letter, Letter.id == DeliveryOrder.letter_id)

    if status is not None:
        stmt = stmt.where(DeliveryOrder.status == status)
        count_stmt = count_stmt.where(DeliveryOrder.status == status)
    if provider_id is not None:
        stmt = stmt.where(DeliveryOrder.provider_id == provider_id)
        count_stmt = count_stmt.where(DeliveryOrder.provider_id == provider_id)
    if courier_id is not None:
        stmt = stmt.where(DeliveryOrder.courier_id == courier_id)
        count_stmt = count_stmt.where(DeliveryOrder.courier_id == courier_id)
    if search:
        pattern = f"%{search}%"
        condition = or_(DeliveryOrder.tracking_number.ilike(pattern), Letter.reference.ilike(pattern))
        stmt = stmt.where(condition)
        count_stmt = count_stmt.where(condition)

    total = db.execute(count_stmt).scalar_one()
    stmt = stmt.order_by(DeliveryOrder.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    items = list(db.execute(stmt).scalars().all())
    return items, total


def count_by_status(db: Session, status: DeliveryStatus) -> int:
    stmt = select(func.count(DeliveryOrder.id)).where(DeliveryOrder.status == status)
    return db.execute(stmt).scalar_one()


def count_all(db: Session) -> int:
    return db.execute(select(func.count(DeliveryOrder.id))).scalar_one()


def create_attempt(db: Session, attempt: DeliveryAttempt) -> DeliveryAttempt:
    db.add(attempt)
    db.flush()
    return attempt


def create_proof(db: Session, proof: ProofOfDelivery) -> ProofOfDelivery:
    db.add(proof)
    db.flush()
    return proof
