from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.enums import ActorType, DocumentSourceType, LetterEventType, LetterStatus
from app.models.letter import Letter
from app.repositories import letter_repository
from app.schemas.letter import LetterCreate
from app.services import audit_service, document_service, pricing_service

settings = get_settings()

# A text-message-only letter has no PDF to count pages from. It is priced as
# the minimum, single-page-equivalent weight bracket (see pricing_service).
TEXT_MESSAGE_PAGE_COUNT = 1


def create_letter(
    db: Session,
    payload: LetterCreate,
    file_bytes: bytes | None = None,
    file_name: str | None = None,
    file_content_type: str | None = None,
) -> Letter:
    has_message = bool(payload.message and payload.message.strip())
    has_file = file_bytes is not None and len(file_bytes) > 0

    if has_message and has_file:
        raise ValidationAppError("Choose either a written message or a PDF upload, not both")
    if not has_message and not has_file:
        raise ValidationAppError("A message or a PDF document is required")

    content_type = DocumentSourceType.PDF_UPLOAD if has_file else DocumentSourceType.TEXT_MESSAGE

    # The backend is the sole source of truth for pricing: page count is
    # always derived here from the actual uploaded bytes, never accepted from
    # the client, and the price is computed from it -- never trusted from
    # the request. See app/services/pricing_service.py.
    if has_file:
        document_service.validate_pdf(file_name or "document.pdf", file_content_type, file_bytes)
        page_count = document_service.count_pdf_pages(file_bytes)
    else:
        page_count = TEXT_MESSAGE_PAGE_COUNT

    breakdown = pricing_service.calculate_letter_price(
        page_count, acknowledgment_of_receipt=payload.acknowledgment_of_receipt
    )

    letter = Letter(
        sender_first_name=payload.sender.first_name,
        sender_last_name=payload.sender.last_name,
        sender_email=payload.sender.email,
        sender_phone=payload.sender.phone,
        recipient_first_name=payload.recipient.first_name,
        recipient_last_name=payload.recipient.last_name,
        recipient_email=payload.recipient.email,
        recipient_phone=payload.recipient.phone,
        subject=payload.subject,
        message=payload.message if has_message else None,
        content_type=content_type,
        status=LetterStatus.DRAFT,
        page_count=breakdown.page_count,
        sheet_count=breakdown.sheet_count,
        printing_mode=breakdown.printing_mode,
        printing_sides=breakdown.printing_sides,
        paper_weight_g=breakdown.paper_weight_g,
        envelope_weight_g=breakdown.envelope_weight_g,
        estimated_weight_g=breakdown.estimated_weight_g,
        weight_bracket=breakdown.weight_bracket,
        printing_cost=breakdown.printing_cost,
        paper_cost=breakdown.paper_cost,
        envelope_cost=breakdown.envelope_cost,
        postal_postage=breakdown.postal_postage,
        registered_mail_fee=breakdown.registered_mail_fee,
        acknowledgment_of_receipt=breakdown.acknowledgment_of_receipt,
        acknowledgment_fee=breakdown.acknowledgment_fee,
        delivery_fee=breakdown.delivery_fee,
        service_fee=breakdown.service_fee,
        total_amount=breakdown.total,
        currency=breakdown.currency,
    )
    letter = letter_repository.create(db, letter)

    if has_file:
        document_service.store_document(db, letter.id, file_name or "document.pdf", file_content_type or "", file_bytes)

    audit_service.record_event(db, letter.id, LetterEventType.LETTER_CREATED, ActorType.SENDER)

    db.commit()
    db.refresh(letter)
    return letter


def get_letter_or_404(db: Session, letter_id: UUID) -> Letter:
    letter = letter_repository.get_by_id_with_document(db, letter_id)
    if letter is None:
        raise NotFoundError("Letter not found")
    return letter


def get_by_reference_or_404(db: Session, reference: str) -> Letter:
    letter = letter_repository.get_by_reference(db, reference)
    if letter is None:
        raise NotFoundError("Letter not found")
    return letter
