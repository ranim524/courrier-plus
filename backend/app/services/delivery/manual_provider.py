from app.models.delivery import DeliveryOrder
from app.services.delivery.base import BaseDeliveryProvider, CarrierTrackingInfo, ShipmentInfo


class ManualDeliveryProvider(BaseDeliveryProvider):
    """Phase 1: no external delivery-company API. All status changes are
    driven directly by admin actions in delivery_service.py -- this class
    has nothing to call out to, so its methods are deliberately no-ops. It
    exists so delivery_service.py and routes/delivery.py already go through
    the BaseDeliveryProvider interface today, and swapping in a real carrier
    later (ExternalCarrierProvider) needs no change above this layer.

    The UI labels this provider "Suivi manuel" -- never implying real-time
    carrier tracking that doesn't exist yet (see docs/architecture.md)."""

    def create_shipment(self, delivery_order: DeliveryOrder) -> ShipmentInfo:
        return ShipmentInfo(external_reference=None)

    def assign_courier(self, delivery_order: DeliveryOrder) -> None:
        return None

    def get_tracking(self, delivery_order: DeliveryOrder) -> CarrierTrackingInfo:
        return CarrierTrackingInfo(status=delivery_order.status, external_reference=None)

    def cancel_shipment(self, delivery_order: DeliveryOrder) -> None:
        return None
