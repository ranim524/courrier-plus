"""Add DEPOSITED delivery status and recipient confirmation step

Splits the final delivery confirmation into two steps: the letter is first
marked DEPOSITED (physically placed in the mailbox, reported by an admin for
the manual provider or by an external carrier's webhook), which emails the
recipient a single-use confirmation link; DELIVERED is then only reached
once the recipient confirms (or an admin force-confirms as a fallback).

New Postgres enum values are added with ALTER TYPE ... ADD VALUE (not
detected by autogenerate, and not created fresh by CREATE TYPE against an
already-migrated database -- see .claude/skills/delivery/SKILL.md and
.claude/skills/testing/SKILL.md's "Postgres enum values" gotcha). Each
ALTER TYPE runs as its own statement, a Postgres requirement.

Revision ID: f1c2b3a4d5e6
Revises: a949d4ca8fb4
Create Date: 2026-09-11
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f1c2b3a4d5e6"
down_revision = "a949d4ca8fb4"
branch_labels = None
depends_on = None

NEW_DELIVERY_STATUS_VALUES = ["DEPOSITED"]
NEW_LETTER_EVENT_TYPE_VALUES = ["DELIVERY_DEPOSITED"]
NEW_EMAIL_TYPE_VALUES = ["DELIVERY_CONFIRMATION_REQUEST"]


def upgrade() -> None:
    # Each ADD VALUE must be its own statement (Postgres restriction).
    # IF NOT EXISTS makes this migration safe to re-run.
    for value in NEW_DELIVERY_STATUS_VALUES:
        op.execute(f"ALTER TYPE delivery_status ADD VALUE IF NOT EXISTS '{value}'")
    for value in NEW_LETTER_EVENT_TYPE_VALUES:
        op.execute(f"ALTER TYPE letter_event_type ADD VALUE IF NOT EXISTS '{value}'")
    for value in NEW_EMAIL_TYPE_VALUES:
        op.execute(f"ALTER TYPE email_type ADD VALUE IF NOT EXISTS '{value}'")

    op.add_column("delivery_orders", sa.Column("deposited_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("delivery_orders", sa.Column("confirmation_token_hash", sa.String(length=64), nullable=True))
    op.create_unique_constraint(
        "uq_delivery_orders_confirmation_token_hash", "delivery_orders", ["confirmation_token_hash"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_delivery_orders_confirmation_token_hash", "delivery_orders", type_="unique")
    op.drop_column("delivery_orders", "confirmation_token_hash")
    op.drop_column("delivery_orders", "deposited_at")
    # Postgres has no DROP VALUE for enum types -- the added labels
    # (DEPOSITED, DELIVERY_DEPOSITED, DELIVERY_CONFIRMATION_REQUEST) are left
    # in place, unused, same as every other enum-add migration in this
    # project.
