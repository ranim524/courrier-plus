"""Physical delivery orchestration.

Owns the DeliveryOrder state machine (see delivery_state.py) and is the only
place that:
  - creates a DeliveryOrder (called once, right after a Letter reaches SENT)
  - moves it through CREATED -> READY_FOR_DISPATCH -> ASSIGNED -> PICKED_UP
    -> IN_TRANSIT -> OUT_FOR_DELIVERY -> DELIVERED (or the failure/return path)
  - creates the ProofOfDelivery and sends the two delivery-confirmed emails,
    exactly once, only when the physical letter is actually confirmed
    DELIVERED -- never on any earlier status (see confirm_delivery below).

All admin-triggered actions go through here; routes/delivery.py never
mutates a DeliveryOrder directly.
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.admin import Admin
from app.models.delivery import DeliveryAttempt, DeliveryOrder, ProofOfDelivery
from app.models.enums import ActorType, DeliveryFailureReason, DeliveryStatus, LetterEventType, LetterStatus
from app.models.letter import Letter
from app.repositories import delivery_provider_repository, delivery_repository
from app.services import audit_service, delivery_state, email_service, letter_state

DEFAULT_PROVIDER_CODE = "courrier_plus_internal"
MAX_TRACKING_NUMBER_ATTEMPTS = 10


def _generate_unique_tracking_number(db: Session) -> str:
    from app.utils.tracking_number import generate_candidate_tracking_number

    for _ in range(MAX_TRACKING_NUMBER_ATTEMPTS):
        candidate = generate_candidate_tracking_number()
        if not delivery_repository.tracking_number_exists(db, candidate):
            return candidate
    raise ConflictError("Could not generate a unique tracking number, please retry")


def create_delivery_order(db: Session, letter: Letter) -> DeliveryOrder:
    """Called once, right after a Letter transitions to SENT (see
    payment_service.confirm_payment). A letter has at most one delivery
    order (unique FK)."""
    provider = delivery_provider_repository.get_by_code(db, DEFAULT_PROVIDER_CODE)
    if provider is None:
        raise NotFoundError("Default delivery provider is not configured")

    order = DeliveryOrder(
        letter_id=letter.id,
        tracking_number=_generate_unique_tracking_number(db),
        provider_id=provider.id,
        status=DeliveryStatus.CREATED,
    )
    order = delivery_repository.create(db, order)
    audit_service.record_event(db, letter.id, LetterEventType.DELIVERY_CREATED, ActorType.SYSTEM)

    # The prototype has no separate "printed"/"prepared" step to wait on, so
    # a freshly created order is immediately ready for an admin to dispatch.
    delivery_state.transition(order, DeliveryStatus.READY_FOR_DISPATCH)
    db.flush()

    return order


def get_delivery_or_404(db: Session, delivery_id: UUID) -> DeliveryOrder:
    order = delivery_repository.get_by_id(db, delivery_id)
    if order is None:
        raise NotFoundError("Delivery not found")
    return order


def get_delivery_for_letter(db: Session, letter_id: UUID) -> DeliveryOrder | None:
    return delivery_repository.get_by_letter_id(db, letter_id)


def _record(db: Session, order: DeliveryOrder, event_type: LetterEventType, admin: Admin | None) -> None:
    actor = ActorType.ADMIN if admin is not None else ActorType.SYSTEM
    audit_service.record_event(db, order.letter_id, event_type, actor)


def assign_courier(db: Session, delivery_id: UUID, agent_id: UUID, admin: Admin) -> DeliveryOrder:
    order = get_delivery_or_404(db, delivery_id)
    delivery_state.transition(order, DeliveryStatus.ASSIGNED)
    order.courier_id = agent_id
    order.assigned_at = datetime.now(timezone.utc)
    _record(db, order, LetterEventType.DELIVERY_ASSIGNED, admin)
    db.commit()
    db.refresh(order)
    return order


def mark_picked_up(db: Session, delivery_id: UUID, admin: Admin) -> DeliveryOrder:
    order = get_delivery_or_404(db, delivery_id)
    delivery_state.transition(order, DeliveryStatus.PICKED_UP)
    order.picked_up_at = datetime.now(timezone.utc)
    _record(db, order, LetterEventType.DELIVERY_PICKED_UP, admin)
    db.commit()
    db.refresh(order)
    return order


def mark_in_transit(db: Session, delivery_id: UUID, admin: Admin) -> DeliveryOrder:
    order = get_delivery_or_404(db, delivery_id)
    delivery_state.transition(order, DeliveryStatus.IN_TRANSIT)
    order.in_transit_at = datetime.now(timezone.utc)
    _record(db, order, LetterEventType.DELIVERY_IN_TRANSIT, admin)
    db.commit()
    db.refresh(order)
    return order


def mark_out_for_delivery(db: Session, delivery_id: UUID, admin: Admin) -> DeliveryOrder:
    order = get_delivery_or_404(db, delivery_id)
    delivery_state.transition(order, DeliveryStatus.OUT_FOR_DELIVERY)
    order.out_for_delivery_at = datetime.now(timezone.utc)
    _record(db, order, LetterEventType.DELIVERY_OUT_FOR_DELIVERY, admin)
    db.commit()
    db.refresh(order)
    return order


def confirm_delivery(
    db: Session, delivery_id: UUID, admin: Admin, notes: str | None = None
) -> DeliveryOrder:
    """The only path that can trigger the final "delivered" notifications.
    Idempotent: confirming an already-DELIVERED order is a pure no-op --
    no duplicate ProofOfDelivery, event, or email (spec section 24/46)."""
    order = get_delivery_or_404(db, delivery_id)

    if order.status == DeliveryStatus.DELIVERED:
        return order

    delivery_state.transition(order, DeliveryStatus.DELIVERED)
    delivered_at = datetime.now(timezone.utc)
    order.delivered_at = delivered_at

    proof = ProofOfDelivery(
        delivery_id=order.id,
        delivered_at=delivered_at,
        delivered_by=admin.email,
        delivery_method="Livraison en main propre",
        notes=notes,
    )
    delivery_repository.create_proof(db, proof)
    _record(db, order, LetterEventType.DELIVERY_DELIVERED, admin)
    db.flush()

    letter = order.letter
    # Best-effort: the recipient may already have progressed the letter past
    # SENT via the independent digital access-link flow (OPENED/RECEIVED).
    # DELIVERED only applies as a forward move from SENT; if it doesn't
    # apply, the DeliveryOrder itself (not Letter.status) remains the
    # authoritative record that the physical letter was delivered.
    if letter.status == LetterStatus.SENT:
        letter_state.transition(letter, LetterStatus.DELIVERED)

    delivered_date = delivered_at.strftime("%d/%m/%Y")
    delivered_time = delivered_at.strftime("%H:%M")
    reference = letter.reference or ""

    email_service.send_delivery_confirmed_recipient(
        db, letter.id, letter.recipient_email, reference, order.tracking_number, delivered_date, delivered_time
    )
    email_service.send_delivery_confirmed_sender(
        db,
        letter.id,
        letter.sender_email,
        letter.sender_first_name,
        reference,
        order.tracking_number,
        delivered_date,
        delivered_time,
        _tracking_url(reference),
    )

    db.commit()
    db.refresh(order)
    return order


def mark_failed(
    db: Session, delivery_id: UUID, reason: DeliveryFailureReason, admin: Admin, notes: str | None = None
) -> DeliveryOrder:
    order = get_delivery_or_404(db, delivery_id)
    delivery_state.transition(order, DeliveryStatus.DELIVERY_FAILED)
    order.failed_at = datetime.now(timezone.utc)
    order.attempt_count += 1

    attempt = DeliveryAttempt(
        delivery_id=order.id,
        attempt_number=order.attempt_count,
        attempted_at=order.failed_at,
        courier_id=order.courier_id,
        reason=reason,
        notes=notes,
    )
    delivery_repository.create_attempt(db, attempt)
    _record(db, order, LetterEventType.DELIVERY_FAILED, admin)
    db.commit()
    db.refresh(order)
    return order


def retry_delivery(db: Session, delivery_id: UUID, admin: Admin) -> DeliveryOrder:
    order = get_delivery_or_404(db, delivery_id)
    delivery_state.transition(order, DeliveryStatus.OUT_FOR_DELIVERY)
    _record(db, order, LetterEventType.DELIVERY_OUT_FOR_DELIVERY, admin)
    db.commit()
    db.refresh(order)
    return order


def return_to_sender(db: Session, delivery_id: UUID, admin: Admin) -> DeliveryOrder:
    order = get_delivery_or_404(db, delivery_id)
    delivery_state.transition(order, DeliveryStatus.RETURNED_TO_SENDER)
    order.returned_at = datetime.now(timezone.utc)
    _record(db, order, LetterEventType.DELIVERY_RETURNED, admin)
    db.commit()
    db.refresh(order)
    return order


def cancel_delivery(db: Session, delivery_id: UUID, admin: Admin) -> DeliveryOrder:
    order = get_delivery_or_404(db, delivery_id)
    delivery_state.transition(order, DeliveryStatus.CANCELLED)
    _record(db, order, LetterEventType.DELIVERY_CANCELLED, admin)
    db.commit()
    db.refresh(order)
    return order


def _tracking_url(reference: str) -> str:
    from app.core.config import get_settings

    return f"{get_settings().frontend_url}/track/{reference}"


def to_summary(order: DeliveryOrder):
    from app.schemas.delivery import DeliveryOrderSummary

    return DeliveryOrderSummary(
        id=order.id,
        tracking_number=order.tracking_number,
        letter_reference=order.letter.reference,
        recipient_name=f"{order.letter.recipient_first_name} {order.letter.recipient_last_name}",
        status=order.status,
        provider_name=order.provider.name,
        courier_name=f"{order.courier.first_name} {order.courier.last_name}" if order.courier else None,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


def to_read(order: DeliveryOrder):
    from app.schemas.delivery import DeliveryAttemptRead, DeliveryOrderRead, ProofOfDeliveryRead

    return DeliveryOrderRead(
        id=order.id,
        letter_id=order.letter_id,
        letter_reference=order.letter.reference,
        tracking_number=order.tracking_number,
        status=order.status,
        provider=order.provider,
        courier=order.courier,
        attempt_count=order.attempt_count,
        created_at=order.created_at,
        assigned_at=order.assigned_at,
        picked_up_at=order.picked_up_at,
        in_transit_at=order.in_transit_at,
        out_for_delivery_at=order.out_for_delivery_at,
        delivered_at=order.delivered_at,
        failed_at=order.failed_at,
        returned_at=order.returned_at,
        updated_at=order.updated_at,
        attempts=[DeliveryAttemptRead.model_validate(a) for a in order.attempts],
        proof=ProofOfDeliveryRead.model_validate(order.proof) if order.proof else None,
    )


_PUBLIC_EVENT_LABELS: list[tuple[str, str]] = [
    ("created_at", "Livraison créée"),
    ("assigned_at", "Affectée au livreur"),
    ("picked_up_at", "Prise en charge"),
    ("in_transit_at", "En transit"),
    ("out_for_delivery_at", "En cours de livraison"),
    ("delivered_at", "Livrée"),
]


def to_public_view(order: DeliveryOrder):
    """Safe subset for the public tracking page / recipient secure-link view
    -- derived only from this order's own timestamp columns, never from
    LetterEvent rows (which may carry admin/actor detail not meant to be
    public). No courier name/phone, no admin notes, no internal IDs."""
    from app.schemas.delivery import DeliveryPublicEvent, DeliveryPublicView

    events = []
    for field, label in _PUBLIC_EVENT_LABELS:
        at = getattr(order, field)
        if at is not None:
            events.append(DeliveryPublicEvent(label=label, at=at))

    return DeliveryPublicView(tracking_number=order.tracking_number, status=order.status, events=events)
