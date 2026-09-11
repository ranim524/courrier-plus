"""Remove digital recipient access (letter opened/received-by-link flow)

The recipient no longer gets any email, or any digital access to a letter's
content, before physical delivery is confirmed by an admin. LetterStatus.OPENED
is removed from the application enum accordingly (RECEIVED is now reached
directly from SENT via delivery_service.confirm_delivery when the paid
acknowledgment-of-receipt option was requested, DELIVERED otherwise).

Any existing letter still sitting in the now-removed OPENED status is
backfilled to SENT -- it was never physically delivered, so this is the
correct forward state under the new model.

The `access_tokens` table and the OPENED/LETTER_OPENED Postgres enum labels
are intentionally left in place: dropping a Postgres enum value isn't
supported, and access_tokens already holds historical audit data that must
not be lost. Nothing in the application writes either going forward.

Revision ID: a949d4ca8fb4
Revises: 43aa24b4be43
Create Date: 2026-09-11
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "a949d4ca8fb4"
down_revision = "43aa24b4be43"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE letters SET status = 'SENT' WHERE status = 'OPENED'")


def downgrade() -> None:
    # Which letters were OPENED before the backfill can't be recovered.
    pass
