from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.models.delivery import DeliveryOrder
from app.models.enums import DeliveryStatus


@dataclass
class ShipmentInfo:
    """Returned by create_shipment(). external_reference is whatever ID the
    external carrier assigns, if any -- None for the manual provider, which
    has no external system to register with."""

    external_reference: str | None


@dataclass
class CarrierTrackingInfo:
    status: DeliveryStatus
    external_reference: str | None


class BaseDeliveryProvider(ABC):
    """Abstraction so a real external carrier can be plugged in later without
    changing delivery_service.py or anything above it (routes, admin UI).
    All status changes for the manual provider come from explicit admin
    actions in delivery_service.py; a future external provider would instead
    drive some of these from its own API/webhook (see routes/delivery.py's
    reserved webhook shape)."""

    @abstractmethod
    def create_shipment(self, delivery_order: DeliveryOrder) -> ShipmentInfo:
        """Registers the shipment with the provider, if it has an external API."""

    @abstractmethod
    def assign_courier(self, delivery_order: DeliveryOrder) -> None:
        """Notifies the provider of the courier assignment, if applicable."""

    @abstractmethod
    def get_tracking(self, delivery_order: DeliveryOrder) -> CarrierTrackingInfo:
        """Returns the provider's view of the current status."""

    @abstractmethod
    def cancel_shipment(self, delivery_order: DeliveryOrder) -> None:
        """Cancels the shipment with the provider, if applicable."""
