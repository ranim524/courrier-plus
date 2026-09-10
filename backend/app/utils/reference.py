import secrets
from datetime import datetime, timezone


def generate_candidate_reference() -> str:
    """Generates a candidate public letter reference like TN-2026-0001847.

    Uniqueness is enforced by the caller (repository) via a DB unique constraint
    + retry loop, not by this function alone.
    """
    year = datetime.now(timezone.utc).year
    suffix = secrets.randbelow(10_000_000)
    return f"TN-{year}-{suffix:07d}"
