from app.services.delivery.base import BaseDeliveryProvider
from app.services.delivery.manual_provider import ManualDeliveryProvider

# Keyed by DeliveryProvider.code (see the seeded "courrier_plus_internal" row
# in the initial delivery migration). A future external carrier registers
# here under its own code -- delivery_service.py never hardcodes a provider.
_PROVIDERS: dict[str, type[BaseDeliveryProvider]] = {
    "courrier_plus_internal": ManualDeliveryProvider,
}


def get_delivery_provider(code: str) -> BaseDeliveryProvider:
    provider_cls = _PROVIDERS.get(code, ManualDeliveryProvider)
    return provider_cls()
