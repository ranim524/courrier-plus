from sqlalchemy.orm import Session

from app.repositories import letter_event_repository
from app.schemas.tracking import TrackingEvent, TrackingRead
from app.services import delivery_service, letter_service


def get_tracking(db: Session, reference: str) -> TrackingRead:
    letter = letter_service.get_by_reference_or_404(db, reference)
    events = letter_event_repository.list_for_letter(db, letter.id)

    delivery_order = delivery_service.get_delivery_for_letter(db, letter.id)
    delivery_view = delivery_service.to_public_view(delivery_order) if delivery_order else None

    return TrackingRead(
        reference=letter.reference or "",
        status=letter.status,
        subject=letter.subject,
        sender_first_name=letter.sender_first_name,
        sender_last_name=letter.sender_last_name,
        recipient_first_name=letter.recipient_first_name,
        recipient_last_name=letter.recipient_last_name,
        created_at=letter.created_at,
        events=[TrackingEvent.model_validate(e) for e in events],
        delivery=delivery_view,
    )
