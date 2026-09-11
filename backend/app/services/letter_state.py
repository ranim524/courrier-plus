from app.core.exceptions import ConflictError
from app.models.enums import LetterStatus
from app.models.letter import Letter

# Explicit allowed transitions. Any transition not listed here is rejected.
ALLOWED_TRANSITIONS: dict[LetterStatus, set[LetterStatus]] = {
    LetterStatus.DRAFT: {LetterStatus.PENDING_PAYMENT, LetterStatus.CANCELLED},
    LetterStatus.PENDING_PAYMENT: {LetterStatus.PAID, LetterStatus.FAILED, LetterStatus.CANCELLED},
    LetterStatus.PAID: {LetterStatus.SENT, LetterStatus.FAILED},
    # The recipient has no digital access to the letter's content -- the only
    # way forward from SENT is a physically confirmed delivery (see
    # delivery_service.confirm_delivery), landing on RECEIVED when the paid
    # acknowledgment-of-receipt option was requested, DELIVERED otherwise.
    LetterStatus.SENT: {LetterStatus.DELIVERED, LetterStatus.RECEIVED, LetterStatus.FAILED},
    LetterStatus.DELIVERED: set(),
    LetterStatus.RECEIVED: set(),
    LetterStatus.FAILED: set(),
    LetterStatus.REFUSED: set(),
    LetterStatus.EXPIRED: set(),
    LetterStatus.CANCELLED: set(),
}


def transition(letter: Letter, new_status: LetterStatus) -> None:
    """Applies a controlled state transition. Raises ConflictError on an invalid move.
    Does not create the audit event itself -- callers add the matching LetterEvent
    in the same transaction so status + event stay consistent."""
    if letter.status == new_status:
        return
    allowed = ALLOWED_TRANSITIONS.get(letter.status, set())
    if new_status not in allowed:
        raise ConflictError(
            f"Cannot transition letter from {letter.status.value} to {new_status.value}"
        )
    letter.status = new_status
