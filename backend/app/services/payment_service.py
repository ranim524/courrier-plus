from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.enums import ActorType, LetterEventType, LetterStatus, PaymentStatus
from app.models.payment import Payment
from app.repositories import letter_repository, payment_repository
from app.services import access_service, audit_service, delivery_service, email_service, letter_state
from app.services.payment import get_payment_provider
from app.utils.reference import generate_candidate_reference

MAX_REFERENCE_ATTEMPTS = 10


def _generate_unique_reference(db: Session) -> str:
    for _ in range(MAX_REFERENCE_ATTEMPTS):
        candidate = generate_candidate_reference()
        if not letter_repository.reference_exists(db, candidate):
            return candidate
    raise ConflictError("Could not generate a unique letter reference, please retry")


def create_payment(db: Session, letter_id: UUID) -> Payment:
    letter = letter_repository.get_by_id(db, letter_id)
    if letter is None:
        raise NotFoundError("Letter not found")

    if letter.status == LetterStatus.DRAFT:
        letter_state.transition(letter, LetterStatus.PENDING_PAYMENT)
        audit_service.record_event(db, letter.id, LetterEventType.PAYMENT_STARTED, ActorType.SENDER)
    elif letter.status != LetterStatus.PENDING_PAYMENT:
        raise ConflictError(f"Cannot start payment for a letter in status {letter.status.value}")

    existing = payment_repository.get_by_letter_id(db, letter.id)
    if existing is not None and existing.status == PaymentStatus.PENDING:
        db.commit()
        return existing

    provider = get_payment_provider()
    intent = provider.create_payment(float(letter.total_amount), letter.currency)

    payment = Payment(
        letter_id=letter.id,
        provider=intent.provider,
        transaction_id=intent.transaction_id,
        amount=intent.amount,
        currency=intent.currency,
        status=PaymentStatus.PENDING,
    )
    payment = payment_repository.create(db, payment)
    db.commit()
    db.refresh(payment)
    return payment


def confirm_payment(db: Session, transaction_id: str, outcome: str) -> Payment:
    payment = payment_repository.get_by_transaction_id(db, transaction_id)
    if payment is None:
        raise NotFoundError("Payment not found")

    # Idempotency: a repeated confirm/webhook call for an already-processed
    # payment must not duplicate the letter activation or emails.
    if payment.status in (PaymentStatus.PAID, PaymentStatus.FAILED):
        return payment

    provider = get_payment_provider()
    result = provider.confirm(transaction_id, outcome)

    letter = letter_repository.get_by_id_with_document(db, payment.letter_id)
    if letter is None:
        raise NotFoundError("Letter not found")

    if result.success:
        payment.status = PaymentStatus.PAID
        letter_state.transition(letter, LetterStatus.PAID)
        audit_service.record_event(db, letter.id, LetterEventType.PAYMENT_SUCCEEDED, ActorType.SYSTEM)

        letter.reference = _generate_unique_reference(db)
        letter_state.transition(letter, LetterStatus.SENT)
        audit_service.record_event(db, letter.id, LetterEventType.LETTER_SENT, ActorType.SYSTEM)
        db.flush()

        # Physical delivery order is created as soon as the letter is sent --
        # see app/services/delivery_service.py for the full state machine.
        delivery_service.create_delivery_order(db, letter)

        raw_token = access_service.create_access_token(db, letter.id)
        access_url = f"{_frontend_access_url(raw_token)}"

        sent_date = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M")
        tracking_url = _frontend_tracking_url(letter.reference)

        email_service.send_payment_confirmation(
            db,
            letter.id,
            letter.sender_email,
            letter.sender_first_name,
            letter.reference,
            f"{letter.recipient_first_name} {letter.recipient_last_name}",
            letter.page_count,
            float(payment.amount),
            payment.currency,
            tracking_url,
            sent_date,
        )
        email_service.send_recipient_notification(
            db,
            letter.id,
            letter.recipient_email,
            f"{letter.sender_first_name} {letter.sender_last_name}",
            letter.subject,
            access_url,
            _expiration_info(),
        )
    else:
        payment.status = PaymentStatus.FAILED
        letter_state.transition(letter, LetterStatus.FAILED)
        audit_service.record_event(db, letter.id, LetterEventType.PAYMENT_FAILED, ActorType.SYSTEM)

    db.commit()
    db.refresh(payment)
    return payment


def _frontend_access_url(raw_token: str) -> str:
    from app.core.config import get_settings

    return f"{get_settings().frontend_url}/access/{raw_token}"


def _frontend_tracking_url(reference: str) -> str:
    from app.core.config import get_settings

    return f"{get_settings().frontend_url}/track/{reference}"


def _expiration_info() -> str:
    from app.core.config import get_settings

    days = get_settings().access_token_expiration_days
    return f"Ce lien est valable {days} jours."
