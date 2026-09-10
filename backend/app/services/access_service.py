from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import ExpiredError, ForbiddenError, NotFoundError
from app.core.security import generate_secure_token, hash_token
from app.models.access_token import AccessToken
from app.models.enums import ActorType, LetterEventType, LetterStatus
from app.models.letter import Letter
from app.repositories import access_token_repository, letter_repository
from app.schemas.tracking import AccessLetterView
from app.services import audit_service, email_service, letter_state

settings = get_settings()


def create_access_token(db: Session, letter_id: UUID) -> str:
    raw_token = generate_secure_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.access_token_expiration_days)
    token = AccessToken(letter_id=letter_id, token_hash=hash_token(raw_token), expires_at=expires_at)
    access_token_repository.create(db, token)
    return raw_token


def _resolve_token(db: Session, raw_token: str) -> tuple[AccessToken, Letter]:
    token = access_token_repository.get_by_token_hash(db, hash_token(raw_token))
    if token is None or token.revoked_at is not None:
        raise NotFoundError("Invalid access link")

    letter = letter_repository.get_by_id_with_document(db, token.letter_id)
    if letter is None:
        raise NotFoundError("Invalid access link")

    if token.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise ExpiredError("This access link has expired")

    if letter.status in (LetterStatus.CANCELLED, LetterStatus.FAILED, LetterStatus.EXPIRED):
        raise ForbiddenError("This letter is no longer accessible")

    return token, letter


def get_letter_for_token(db: Session, raw_token: str) -> Letter:
    """Resolves a token to its letter without recording an access event.
    Used for actions like document download that follow an already-recorded view."""
    _, letter = _resolve_token(db, raw_token)
    return letter


def view_letter(db: Session, raw_token: str, ip_address: str | None, user_agent: str | None) -> AccessLetterView:
    token, letter = _resolve_token(db, raw_token)

    token.last_used_at = datetime.now(timezone.utc)
    audit_service.record_event(
        db, letter.id, LetterEventType.RECIPIENT_LINK_ACCESSED, ActorType.RECIPIENT, ip_address, user_agent
    )
    db.commit()

    return AccessLetterView(
        reference=letter.reference or "",
        sender_first_name=letter.sender_first_name,
        sender_last_name=letter.sender_last_name,
        subject=letter.subject,
        message=letter.message,
        status=letter.status,
        has_document=letter.document is not None,
        created_at=letter.created_at,
    )


def mark_opened(db: Session, raw_token: str, ip_address: str | None, user_agent: str | None) -> AccessLetterView:
    token, letter = _resolve_token(db, raw_token)

    if letter.status in (LetterStatus.SENT, LetterStatus.DELIVERED):
        letter_state.transition(letter, LetterStatus.OPENED)
        audit_service.record_event(db, letter.id, LetterEventType.LETTER_OPENED, ActorType.RECIPIENT, ip_address, user_agent)
        db.flush()

        opened_at = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M")
        email_service.send_letter_opened(
            db, letter.id, letter.sender_email, letter.sender_first_name, letter.reference or "", opened_at
        )

    db.commit()
    db.refresh(letter)

    return AccessLetterView(
        reference=letter.reference or "",
        sender_first_name=letter.sender_first_name,
        sender_last_name=letter.sender_last_name,
        subject=letter.subject,
        message=letter.message,
        status=letter.status,
        has_document=letter.document is not None,
        created_at=letter.created_at,
    )


def confirm_receipt(db: Session, raw_token: str, ip_address: str | None, user_agent: str | None) -> AccessLetterView:
    token, letter = _resolve_token(db, raw_token)

    if letter.status != LetterStatus.RECEIVED:
        letter_state.transition(letter, LetterStatus.RECEIVED)
        audit_service.record_event(
            db,
            letter.id,
            LetterEventType.RECEIPT_CONFIRMED,
            ActorType.RECIPIENT,
            ip_address,
            user_agent,
        )
        db.flush()

        confirmed_at = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M")
        email_service.send_receipt_confirmed(
            db, letter.id, letter.sender_email, letter.sender_first_name, letter.reference or "", confirmed_at
        )

    db.commit()
    db.refresh(letter)

    return AccessLetterView(
        reference=letter.reference or "",
        sender_first_name=letter.sender_first_name,
        sender_last_name=letter.sender_last_name,
        subject=letter.subject,
        message=letter.message,
        status=letter.status,
        has_document=letter.document is not None,
        created_at=letter.created_at,
    )
