from app.core.config import get_settings
from app.services.payment.base import PaymentProvider
from app.services.payment.mock_provider import MockPaymentProvider

settings = get_settings()

_PROVIDERS: dict[str, type[PaymentProvider]] = {
    "mock": MockPaymentProvider,
}


def get_payment_provider() -> PaymentProvider:
    provider_cls = _PROVIDERS.get(settings.payment_provider, MockPaymentProvider)
    return provider_cls()
