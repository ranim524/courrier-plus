from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.enums import ActorType, DocumentSourceType, LetterEventType, LetterStatus
from app.models.letter import Letter
from app.repositories import letter_repository
from app.schemas.letter import LetterCreate
from app.services import audit_service, document_service

settings = get_settings()


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
        price=settings.letter_price,
        currency=settings.currency,
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
