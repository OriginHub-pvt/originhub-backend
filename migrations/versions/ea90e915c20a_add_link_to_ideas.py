"""Add link column to ideas table

Revision ID: ea90e915c20a
Revises: 72f39089bf0c
Create Date: 2025-01-27 13:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ea90e915c20a"
down_revision: Union[str, None] = "72f39089bf0c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add link column to ideas table
    op.add_column("ideas", sa.Column("link", sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove link column from ideas table
    op.drop_column("ideas", "link")
