import hmac

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.exceptions import UnauthorizedError
from app.core.rate_limit import limiter
from app.schemas.delivery import DeliveryOrderRead, DeliveryWebhookRequest
from app.services import delivery_service

router = APIRouter(prefix="/api/webhooks/delivery", tags=["delivery-webhook"])


def _verify_webhook_secret(x_webhook_secret: str | None) -> None:
    """Constant-time comparison against DELIVERY_WEBHOOK_SECRET (see
    core/config.py). No carrier credentials are ever stored on
    DeliveryProvider rows -- this is the one shared secret a carrier's
    platform authenticates with, configured only via an env var. An empty
    configured secret means no external carrier is set up yet, so every
    call is rejected rather than silently accepted."""
    settings = get_settings()
    if not settings.delivery_webhook_secret or not x_webhook_secret:
        raise UnauthorizedError("Invalid webhook credentials")
    if not hmac.compare_digest(x_webhook_secret, settings.delivery_webhook_secret):
        raise UnauthorizedError("Invalid webhook credentials")


@router.post("/deposited", response_model=DeliveryOrderRead)
@limiter.limit("60/minute")
def report_deposited(
    request: Request,
    payload: DeliveryWebhookRequest,
    db: Session = Depends(get_db),
    x_webhook_secret: str | None = Header(default=None),
) -> DeliveryOrderRead:
    """Called by an external carrier's own platform (not our admin UI) once
    their courier reports the letter placed in the recipient's mailbox --
    the manual/internal provider uses the equivalent admin action instead
    (POST /api/admin/deliveries/{id}/deposit). Triggers the recipient's
    confirmation email; never notifies the sender directly."""
    _verify_webhook_secret(x_webhook_secret)
    order = delivery_service.mark_deposited_by_tracking_number(db, payload.provider_code, payload.tracking_number)
    return delivery_service.to_read(order)
