from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.email_event import EmailEvent
from app.models.enums import EmailStatus, EmailType
from app.repositories import email_event_repository
from app.services.email_templates.delivery_confirmation_request import render_delivery_confirmation_request
from app.services.email_templates.delivery_confirmed_recipient import render_delivery_confirmed_recipient
from app.services.email_templates.delivery_confirmed_sender import render_delivery_confirmed_sender
from app.services.email_templates.payment_confirmation import render_payment_confirmation
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
    page_count: int,
    amount: float,
    currency: str,
    tracking_url: str,
    sent_date: str,
) -> EmailEvent:
    subject, html = render_payment_confirmation(
        sender_first_name, reference, recipient_full_name, page_count, amount, currency, tracking_url, sent_date
    )
    return _send(db, letter_id, EmailType.PAYMENT_CONFIRMATION, sender_email, subject, html)


def send_system_error(db: Session, letter_id: UUID, admin_email: str, reference: str, error_summary: str) -> EmailEvent:
    subject, html = render_system_error(reference, error_summary)
    return _send(db, letter_id, EmailType.SYSTEM_ERROR, admin_email, subject, html)


def send_delivery_confirmation_request(
    db: Session, letter_id: UUID, recipient_email: str, reference: str, confirm_url: str
) -> EmailEvent:
    subject, html = render_delivery_confirmation_request(reference, confirm_url)
    return _send(db, letter_id, EmailType.DELIVERY_CONFIRMATION_REQUEST, recipient_email, subject, html)


def send_delivery_confirmed_recipient(
    db: Session,
    letter_id: UUID,
    recipient_email: str,
    reference: str,
    tracking_number: str,
    delivered_date: str,
    delivered_time: str,
) -> EmailEvent:
    subject, html = render_delivery_confirmed_recipient(reference, tracking_number, delivered_date, delivered_time)
    return _send(db, letter_id, EmailType.DELIVERY_CONFIRMED_RECIPIENT, recipient_email, subject, html)


def send_delivery_confirmed_sender(
    db: Session,
    letter_id: UUID,
    sender_email: str,
    sender_first_name: str,
    reference: str,
    tracking_number: str,
    delivered_date: str,
    delivered_time: str,
    tracking_url: str,
) -> EmailEvent:
    subject, html = render_delivery_confirmed_sender(
        sender_first_name, reference, tracking_number, delivered_date, delivered_time, tracking_url
    )
    return _send(db, letter_id, EmailType.DELIVERY_CONFIRMED_SENDER, sender_email, subject, html)
