import secrets
from datetime import datetime, timezone


def generate_candidate_tracking_number() -> str:
    """Generates a candidate physical-delivery tracking number like
    CP-2026-0001847 -- distinct from the letter's own public reference
    (TN-2026-...), since a delivery is tracked separately from the letter
    record itself.

    Uniqueness is enforced by the caller (repository) via a DB unique
    constraint + retry loop, not by this function alone.
    """
    year = datetime.now(timezone.utc).year
    suffix = secrets.randbelow(10_000_000)
    return f"CP-{year}-{suffix:07d}"
