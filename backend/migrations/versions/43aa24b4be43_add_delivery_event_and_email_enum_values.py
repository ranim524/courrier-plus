"""add delivery event and email enum values

Revision ID: 43aa24b4be43
Revises: eb4a50b374cf
Create Date: 2026-09-11 14:40:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '43aa24b4be43'
down_revision: Union[str, None] = 'eb4a50b374cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Adding a Python-side enum member (app/models/enums.py) does NOT alter the
# actual Postgres enum type -- that needs an explicit ALTER TYPE per new
# value. Missing this migration is exactly what broke delivery event/email
# recording when this was first tested live (DataError: invalid input value
# for enum letter_event_type: "DELIVERY_CREATED").
LETTER_EVENT_TYPE_VALUES = [
    "DELIVERY_CREATED",
    "DELIVERY_ASSIGNED",
    "DELIVERY_PICKED_UP",
    "DELIVERY_IN_TRANSIT",
    "DELIVERY_OUT_FOR_DELIVERY",
    "DELIVERY_FAILED",
    "DELIVERY_DELIVERED",
    "DELIVERY_RETURNED",
    "DELIVERY_CANCELLED",
]

EMAIL_TYPE_VALUES = [
    "DELIVERY_CONFIRMED_RECIPIENT",
    "DELIVERY_CONFIRMED_SENDER",
]


def upgrade() -> None:
    # Each ADD VALUE must be its own statement (Postgres restriction).
    # IF NOT EXISTS makes this migration safe to re-run.
    for value in LETTER_EVENT_TYPE_VALUES:
        op.execute(f"ALTER TYPE letter_event_type ADD VALUE IF NOT EXISTS '{value}'")
    for value in EMAIL_TYPE_VALUES:
        op.execute(f"ALTER TYPE email_type ADD VALUE IF NOT EXISTS '{value}'")


def downgrade() -> None:
    # PostgreSQL has no ALTER TYPE ... DROP VALUE. Removing enum values
    # requires recreating the type (rewriting every dependent column), which
    # is a much larger operation than this prototype's migrations otherwise
    # need -- deliberately left as a documented no-op rather than attempting
    # a risky type-recreation dance here.
    pass
