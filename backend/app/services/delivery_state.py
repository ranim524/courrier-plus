from app.core.exceptions import ConflictError
from app.models.delivery import DeliveryOrder
from app.models.enums import DeliveryStatus

# Explicit allowed transitions. Any transition not listed here is rejected.
# DELIVERED is strictly terminal: no administrative "undo" is implemented
# (see spec section 15 -- an override mechanism is a deliberate non-goal for
# this prototype, not an oversight).
#
# DEPOSITED sits between OUT_FOR_DELIVERY and DELIVERED: it means the letter
# was physically placed in the recipient's mailbox (reported either by an
# admin for the manual/internal provider, or by an external carrier's own
# platform via a webhook -- see delivery_service.mark_deposited), but the
# recipient hasn't confirmed receipt yet. DELIVERED is only ever reached
# from DEPOSITED, via the recipient's own confirmation click or an admin's
# manual override if the recipient never responds (see
# delivery_service.confirm_delivery_by_recipient / force_confirm_delivery).
ALLOWED_TRANSITIONS: dict[DeliveryStatus, set[DeliveryStatus]] = {
    DeliveryStatus.CREATED: {DeliveryStatus.READY_FOR_DISPATCH, DeliveryStatus.CANCELLED},
    DeliveryStatus.READY_FOR_DISPATCH: {DeliveryStatus.ASSIGNED, DeliveryStatus.CANCELLED},
    DeliveryStatus.ASSIGNED: {DeliveryStatus.PICKED_UP, DeliveryStatus.CANCELLED},
    DeliveryStatus.PICKED_UP: {DeliveryStatus.IN_TRANSIT},
    DeliveryStatus.IN_TRANSIT: {DeliveryStatus.OUT_FOR_DELIVERY},
    DeliveryStatus.OUT_FOR_DELIVERY: {DeliveryStatus.DEPOSITED, DeliveryStatus.DELIVERY_FAILED},
    DeliveryStatus.DEPOSITED: {DeliveryStatus.DELIVERED},
    DeliveryStatus.DELIVERY_FAILED: {DeliveryStatus.OUT_FOR_DELIVERY, DeliveryStatus.RETURNED_TO_SENDER},
    DeliveryStatus.RETURNED_TO_SENDER: set(),
    DeliveryStatus.DELIVERED: set(),
    DeliveryStatus.CANCELLED: set(),
}


def transition(delivery_order: DeliveryOrder, new_status: DeliveryStatus) -> None:
    """Applies a controlled state transition. Raises ConflictError on an
    invalid move. Does not create the audit event or set timestamp columns
    itself -- callers (delivery_service.py) do both in the same transaction
    so status + event + timestamp stay consistent."""
    if delivery_order.status == new_status:
        return
    allowed = ALLOWED_TRANSITIONS.get(delivery_order.status, set())
    if new_status not in allowed:
        raise ConflictError(
            f"Cannot transition delivery from {delivery_order.status.value} to {new_status.value}"
        )
    delivery_order.status = new_status
