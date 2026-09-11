from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.models.admin import Admin
from app.models.enums import DeliveryStatus
from app.repositories import delivery_agent_repository, delivery_provider_repository, delivery_repository
from app.schemas.common import Page
from app.schemas.delivery import (
    AssignCourierRequest,
    DeliveryAgentCreate,
    DeliveryAgentRead,
    DeliveryAgentUpdate,
    DeliveryConfirmRequest,
    DeliveryFailureRequest,
    DeliveryOrderRead,
    DeliveryOrderSummary,
    DeliveryProviderRead,
)
from app.services import delivery_service

router = APIRouter(prefix="/api/admin/deliveries", tags=["admin-delivery"])
providers_router = APIRouter(prefix="/api/admin/delivery-providers", tags=["admin-delivery"])
agents_router = APIRouter(prefix="/api/admin/delivery-agents", tags=["admin-delivery"])


@router.get("", response_model=Page[DeliveryOrderSummary])
def list_deliveries(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: DeliveryStatus | None = Query(default=None),
    provider_id: UUID | None = Query(default=None),
    courier_id: UUID | None = Query(default=None),
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
) -> Page[DeliveryOrderSummary]:
    items, total = delivery_repository.list_deliveries(db, page, page_size, status, provider_id, courier_id, search)
    total_pages = max(1, (total + page_size - 1) // page_size)
    return Page[DeliveryOrderSummary](
        items=[delivery_service.to_summary(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{delivery_id}", response_model=DeliveryOrderRead)
def get_delivery(delivery_id: UUID, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)) -> DeliveryOrderRead:
    order = delivery_service.get_delivery_or_404(db, delivery_id)
    return delivery_service.to_read(order)


@router.post("/{delivery_id}/assign", response_model=DeliveryOrderRead)
def assign_courier(
    delivery_id: UUID, payload: AssignCourierRequest, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)
) -> DeliveryOrderRead:
    order = delivery_service.assign_courier(db, delivery_id, payload.agent_id, admin)
    return delivery_service.to_read(order)


@router.post("/{delivery_id}/pickup", response_model=DeliveryOrderRead)
def mark_picked_up(delivery_id: UUID, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)) -> DeliveryOrderRead:
    order = delivery_service.mark_picked_up(db, delivery_id, admin)
    return delivery_service.to_read(order)


@router.post("/{delivery_id}/in-transit", response_model=DeliveryOrderRead)
def mark_in_transit(delivery_id: UUID, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)) -> DeliveryOrderRead:
    order = delivery_service.mark_in_transit(db, delivery_id, admin)
    return delivery_service.to_read(order)


@router.post("/{delivery_id}/out-for-delivery", response_model=DeliveryOrderRead)
def mark_out_for_delivery(delivery_id: UUID, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)) -> DeliveryOrderRead:
    order = delivery_service.mark_out_for_delivery(db, delivery_id, admin)
    return delivery_service.to_read(order)


@router.post("/{delivery_id}/deposit", response_model=DeliveryOrderRead)
def mark_deposited(delivery_id: UUID, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)) -> DeliveryOrderRead:
    """Admin-side equivalent of the external-carrier webhook (see
    routes/delivery_webhook.py) for the manual/internal provider: the letter
    was physically placed in the mailbox. Emails the recipient a
    confirmation link -- does NOT notify the sender yet."""
    order = delivery_service.mark_deposited(db, delivery_id, admin)
    return delivery_service.to_read(order)


@router.post("/{delivery_id}/force-confirm", response_model=DeliveryOrderRead)
def force_confirm_delivery(
    delivery_id: UUID,
    payload: DeliveryConfirmRequest,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
) -> DeliveryOrderRead:
    """Fallback when the recipient never clicks their confirmation link.
    Idempotent: confirming an already-DELIVERED order is a no-op, never
    duplicates the proof/event/notification email (spec section 24/46)."""
    order = delivery_service.force_confirm_delivery(db, delivery_id, admin, payload.notes)
    return delivery_service.to_read(order)


@router.post("/{delivery_id}/fail", response_model=DeliveryOrderRead)
def mark_failed(
    delivery_id: UUID, payload: DeliveryFailureRequest, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)
) -> DeliveryOrderRead:
    order = delivery_service.mark_failed(db, delivery_id, payload.reason, admin, payload.notes)
    return delivery_service.to_read(order)


@router.post("/{delivery_id}/retry", response_model=DeliveryOrderRead)
def retry_delivery(delivery_id: UUID, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)) -> DeliveryOrderRead:
    order = delivery_service.retry_delivery(db, delivery_id, admin)
    return delivery_service.to_read(order)


@router.post("/{delivery_id}/return", response_model=DeliveryOrderRead)
def return_to_sender(delivery_id: UUID, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)) -> DeliveryOrderRead:
    order = delivery_service.return_to_sender(db, delivery_id, admin)
    return delivery_service.to_read(order)


@router.post("/{delivery_id}/cancel", response_model=DeliveryOrderRead)
def cancel_delivery(delivery_id: UUID, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)) -> DeliveryOrderRead:
    order = delivery_service.cancel_delivery(db, delivery_id, admin)
    return delivery_service.to_read(order)


@providers_router.get("", response_model=list[DeliveryProviderRead])
def list_providers(db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)) -> list[DeliveryProviderRead]:
    providers = delivery_provider_repository.list_all(db)
    return [DeliveryProviderRead.model_validate(p) for p in providers]


@agents_router.get("", response_model=list[DeliveryAgentRead])
def list_agents(db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)) -> list[DeliveryAgentRead]:
    agents = delivery_agent_repository.list_all(db)
    return [DeliveryAgentRead.model_validate(a) for a in agents]


@agents_router.post("", response_model=DeliveryAgentRead, status_code=201)
def create_agent(
    payload: DeliveryAgentCreate, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)
) -> DeliveryAgentRead:
    from app.models.delivery import DeliveryAgent

    agent = DeliveryAgent(
        provider_id=payload.provider_id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        phone=payload.phone,
        email=payload.email,
    )
    agent = delivery_agent_repository.create(db, agent)
    db.commit()
    db.refresh(agent)
    return DeliveryAgentRead.model_validate(agent)


@agents_router.patch("/{agent_id}", response_model=DeliveryAgentRead)
def update_agent(
    agent_id: UUID, payload: DeliveryAgentUpdate, db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)
) -> DeliveryAgentRead:
    from app.core.exceptions import NotFoundError

    agent = delivery_agent_repository.get_by_id(db, agent_id)
    if agent is None:
        raise NotFoundError("Delivery agent not found")
    agent.active = payload.active
    db.commit()
    db.refresh(agent)
    return DeliveryAgentRead.model_validate(agent)
