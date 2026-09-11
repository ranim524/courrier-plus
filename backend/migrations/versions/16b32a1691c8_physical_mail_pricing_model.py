"""physical mail pricing model

Revision ID: 16b32a1691c8
Revises: 8e320e6b1670
Create Date: 2026-09-11 13:55:24.974730

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '16b32a1691c8'
down_revision: Union[str, None] = '8e320e6b1670'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add every new pricing-breakdown column as nullable first, backfill any
    # existing rows (priced under the previous digital weight-based model,
    # which had no printing/paper/envelope/delivery/service breakdown), then
    # tighten to NOT NULL. total_amount itself is left untouched -- old
    # letters keep the exact price they were actually charged; this backfill
    # only fills in the new descriptive breakdown columns as a reasonable
    # best-effort reconstruction (simplex, black & white, postage/
    # registered-fee carried over from the old base_postage/registered_fee
    # columns), not a source of truth for what was actually charged.
    op.add_column('letters', sa.Column('sheet_count', sa.Integer(), nullable=True))
    op.add_column('letters', sa.Column('printing_mode', sa.String(length=20), nullable=True))
    op.add_column('letters', sa.Column('printing_sides', sa.String(length=10), nullable=True))
    op.add_column('letters', sa.Column('paper_weight_g', sa.Numeric(precision=10, scale=3), nullable=True))
    op.add_column('letters', sa.Column('envelope_weight_g', sa.Numeric(precision=10, scale=3), nullable=True))
    op.add_column('letters', sa.Column('printing_cost', sa.Numeric(precision=10, scale=3), nullable=True))
    op.add_column('letters', sa.Column('paper_cost', sa.Numeric(precision=10, scale=3), nullable=True))
    op.add_column('letters', sa.Column('envelope_cost', sa.Numeric(precision=10, scale=3), nullable=True))
    op.add_column('letters', sa.Column('postal_postage', sa.Numeric(precision=10, scale=3), nullable=True))
    op.add_column('letters', sa.Column('registered_mail_fee', sa.Numeric(precision=10, scale=3), nullable=True))
    op.add_column('letters', sa.Column('delivery_fee', sa.Numeric(precision=10, scale=3), nullable=True))
    op.add_column('letters', sa.Column('service_fee', sa.Numeric(precision=10, scale=3), nullable=True))

    op.execute(
        """
        UPDATE letters SET
            sheet_count = page_count,
            printing_mode = 'black_and_white',
            printing_sides = 'single',
            paper_weight_g = page_count * 5.000,
            envelope_weight_g = 10.000,
            printing_cost = page_count * 0.150,
            paper_cost = page_count * 0.050,
            envelope_cost = 0.500,
            postal_postage = base_postage,
            registered_mail_fee = registered_fee,
            delivery_fee = 0.000,
            service_fee = 1.000
        WHERE sheet_count IS NULL
        """
    )

    op.alter_column('letters', 'sheet_count', nullable=False)
    op.alter_column('letters', 'printing_mode', nullable=False)
    op.alter_column('letters', 'printing_sides', nullable=False)
    op.alter_column('letters', 'paper_weight_g', nullable=False)
    op.alter_column('letters', 'envelope_weight_g', nullable=False)
    op.alter_column('letters', 'printing_cost', nullable=False)
    op.alter_column('letters', 'paper_cost', nullable=False)
    op.alter_column('letters', 'envelope_cost', nullable=False)
    op.alter_column('letters', 'postal_postage', nullable=False)
    op.alter_column('letters', 'registered_mail_fee', nullable=False)
    op.alter_column('letters', 'delivery_fee', nullable=False)
    op.alter_column('letters', 'service_fee', nullable=False)

    # estimated_weight_g now includes envelope weight under the new model
    # (old value was page_count * 5g only, no envelope) -- recompute it from
    # the just-backfilled paper/envelope weights for consistency with the
    # new formula, since (unlike total_amount) this is a derived display
    # field, not something a sender was actually charged against.
    op.alter_column('letters', 'estimated_weight_g',
               existing_type=sa.INTEGER(),
               type_=sa.Numeric(precision=10, scale=3),
               existing_nullable=False)
    op.execute("UPDATE letters SET estimated_weight_g = paper_weight_g + envelope_weight_g")

    op.drop_column('letters', 'base_postage')
    op.drop_column('letters', 'registered_fee')


def downgrade() -> None:
    op.add_column('letters', sa.Column('registered_fee', sa.NUMERIC(precision=10, scale=3), autoincrement=False, nullable=True))
    op.add_column('letters', sa.Column('base_postage', sa.NUMERIC(precision=10, scale=3), autoincrement=False, nullable=True))
    op.execute("UPDATE letters SET base_postage = postal_postage, registered_fee = registered_mail_fee")
    op.alter_column('letters', 'base_postage', nullable=False)
    op.alter_column('letters', 'registered_fee', nullable=False)

    op.alter_column('letters', 'estimated_weight_g',
               existing_type=sa.Numeric(precision=10, scale=3),
               type_=sa.INTEGER(),
               existing_nullable=False)
    op.drop_column('letters', 'service_fee')
    op.drop_column('letters', 'delivery_fee')
    op.drop_column('letters', 'registered_mail_fee')
    op.drop_column('letters', 'postal_postage')
    op.drop_column('letters', 'envelope_cost')
    op.drop_column('letters', 'paper_cost')
    op.drop_column('letters', 'printing_cost')
    op.drop_column('letters', 'envelope_weight_g')
    op.drop_column('letters', 'paper_weight_g')
    op.drop_column('letters', 'printing_sides')
    op.drop_column('letters', 'printing_mode')
    op.drop_column('letters', 'sheet_count')
