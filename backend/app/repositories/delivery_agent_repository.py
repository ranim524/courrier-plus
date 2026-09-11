from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.delivery import DeliveryAgent


def create(db: Session, agent: DeliveryAgent) -> DeliveryAgent:
    db.add(agent)
    db.flush()
    return agent


def get_by_id(db: Session, agent_id: UUID) -> DeliveryAgent | None:
    return db.get(DeliveryAgent, agent_id)


def list_all(db: Session, active_only: bool = False) -> list[DeliveryAgent]:
    stmt = select(DeliveryAgent).order_by(DeliveryAgent.last_name, DeliveryAgent.first_name)
    if active_only:
        stmt = stmt.where(DeliveryAgent.active.is_(True))
    return list(db.execute(stmt).scalars().all())
