"""dynamic pricing engine

Revision ID: 62cdd8689b82
Revises: 7f2af88c828a
Create Date: 2026-09-11 00:08:50.898555

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '62cdd8689b82'
down_revision: Union[str, None] = '7f2af88c828a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add the new pricing-breakdown columns as nullable first, backfill any
    # existing rows with the minimum-bracket, no-AR defaults (equivalent to
    # what a 1-page/5g letter would have cost), then tighten to NOT NULL.
    # This preserves any letters created under the old flat-price model
    # instead of requiring the table to be empty.
    op.add_column('letters', sa.Column('page_count', sa.Integer(), nullable=True))
    op.add_column('letters', sa.Column('estimated_weight_g', sa.Integer(), nullable=True))
    op.add_column('letters', sa.Column('weight_bracket', sa.String(length=20), nullable=True))
    op.add_column('letters', sa.Column('base_postage', sa.Numeric(precision=10, scale=3), nullable=True))
    op.add_column('letters', sa.Column('registered_fee', sa.Numeric(precision=10, scale=3), nullable=True))
    op.add_column('letters', sa.Column('acknowledgment_of_receipt', sa.Boolean(), nullable=True))
    op.add_column('letters', sa.Column('acknowledgment_fee', sa.Numeric(precision=10, scale=3), nullable=True))
    op.add_column('letters', sa.Column('total_amount', sa.Numeric(precision=10, scale=3), nullable=True))

    op.execute(
        """
        UPDATE letters SET
            page_count = 1,
            estimated_weight_g = 5,
            weight_bracket = '0-20g',
            base_postage = 0.750,
            registered_fee = 3.000,
            acknowledgment_of_receipt = false,
            acknowledgment_fee = 0.000,
            total_amount = price
        WHERE total_amount IS NULL
        """
    )

    op.alter_column('letters', 'page_count', nullable=False)
    op.alter_column('letters', 'estimated_weight_g', nullable=False)
    op.alter_column('letters', 'weight_bracket', nullable=False)
    op.alter_column('letters', 'base_postage', nullable=False)
    op.alter_column('letters', 'registered_fee', nullable=False)
    op.alter_column('letters', 'acknowledgment_of_receipt', nullable=False)
    op.alter_column('letters', 'acknowledgment_fee', nullable=False)
    op.alter_column('letters', 'total_amount', nullable=False)

    op.drop_column('letters', 'price')


def downgrade() -> None:
    op.add_column('letters', sa.Column('price', sa.NUMERIC(precision=10, scale=2), autoincrement=False, nullable=True))
    op.execute("UPDATE letters SET price = total_amount")
    op.alter_column('letters', 'price', nullable=False)

    op.drop_column('letters', 'total_amount')
    op.drop_column('letters', 'acknowledgment_fee')
    op.drop_column('letters', 'acknowledgment_of_receipt')
    op.drop_column('letters', 'registered_fee')
    op.drop_column('letters', 'base_postage')
    op.drop_column('letters', 'weight_bracket')
    op.drop_column('letters', 'estimated_weight_g')
    op.drop_column('letters', 'page_count')
