from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.email_event import EmailEvent
from app.models.enums import EmailStatus, EmailType
from app.repositories import email_event_repository
from app.services.email_templates.letter_opened import render_letter_opened
from app.services.email_templates.payment_confirmation import render_payment_confirmation
from app.services.email_templates.receipt_confirmed import render_receipt_confirmed
from app.services.email_templates.recipient_notification import render_recipient_notification
from app.services.email_templates.system_error import render_system_error

settings = get_settings()
logger = get_logger(__name__)


def _send(db: Session, letter_id: UUID, email_type: EmailType, recipient: str, subject: str, html: str) -> EmailEvent:
    event = EmailEvent(
        letter_id=letter_id,
        email_type=email_type,
        recipient=recipient,
        status=EmailStatus.PENDING,
    )
    event = email_event_repository.create(db, event)

    if settings.is_email_mock_mode:
        logger.info("MOCK EMAIL [%s] to=%s subject=%s", email_type.value, recipient, subject)
        event.status = EmailStatus.SENT
        event.provider_message_id = "mock"
        return event

    try:
        import resend

        resend.api_key = settings.resend_api_key
        result = resend.Emails.send(
            {
                "from": f"{settings.resend_from_name} <{settings.resend_from_email}>",
                "to": [recipient],
                "subject": subject,
                "html": html,
            }
        )
        event.status = EmailStatus.SENT
        event.provider_message_id = result.get("id") if isinstance(result, dict) else None
    except Exception as exc:  # noqa: BLE001 - email failures must never crash the caller
        logger.error("Resend send failed for %s email to %s: %s", email_type.value, recipient, exc)
        event.status = EmailStatus.FAILED
        event.error_message = str(exc)[:500]

    return event


def send_payment_confirmation(
    db: Session,
    letter_id: UUID,
    sender_email: str,
    sender_first_name: str,
    reference: str,
    recipient_full_name: str,
    amount: float,
    currency: str,
    tracking_url: str,
    sent_date: str,
) -> EmailEvent:
    subject, html = render_payment_confirmation(
        sender_first_name, reference, recipient_full_name, amount, currency, tracking_url, sent_date
    )
    return _send(db, letter_id, EmailType.PAYMENT_CONFIRMATION, sender_email, subject, html)


def send_recipient_notification(
    db: Session,
    letter_id: UUID,
    recipient_email: str,
    sender_full_name: str,
    subject_line: str,
    access_url: str,
    expiration_info: str,
) -> EmailEvent:
    subject, html = render_recipient_notification(sender_full_name, subject_line, access_url, expiration_info)
    return _send(db, letter_id, EmailType.RECIPIENT_NOTIFICATION, recipient_email, subject, html)


def send_letter_opened(
    db: Session, letter_id: UUID, sender_email: str, sender_first_name: str, reference: str, opened_at: str
) -> EmailEvent:
    subject, html = render_letter_opened(sender_first_name, reference, opened_at)
    return _send(db, letter_id, EmailType.LETTER_OPENED, sender_email, subject, html)


def send_receipt_confirmed(
    db: Session, letter_id: UUID, sender_email: str, sender_first_name: str, reference: str, confirmed_at: str
) -> EmailEvent:
    subject, html = render_receipt_confirmed(sender_first_name, reference, confirmed_at)
    return _send(db, letter_id, EmailType.RECEIPT_CONFIRMED, sender_email, subject, html)


def send_system_error(db: Session, letter_id: UUID, admin_email: str, reference: str, error_summary: str) -> EmailEvent:
    subject, html = render_system_error(reference, error_summary)
    return _send(db, letter_id, EmailType.SYSTEM_ERROR, admin_email, subject, html)
