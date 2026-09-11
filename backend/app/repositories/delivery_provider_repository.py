from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.delivery import DeliveryProvider


def get_by_id(db: Session, provider_id: UUID) -> DeliveryProvider | None:
    return db.get(DeliveryProvider, provider_id)


def get_by_code(db: Session, code: str) -> DeliveryProvider | None:
    stmt = select(DeliveryProvider).where(DeliveryProvider.code == code)
    return db.execute(stmt).scalar_one_or_none()


def list_all(db: Session, active_only: bool = False) -> list[DeliveryProvider]:
    stmt = select(DeliveryProvider).order_by(DeliveryProvider.name)
    if active_only:
        stmt = stmt.where(DeliveryProvider.active.is_(True))
    return list(db.execute(stmt).scalars().all())
