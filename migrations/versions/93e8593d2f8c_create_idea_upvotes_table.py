"""create_idea_upvotes_table

Revision ID: 93e8593d2f8c
Revises: 62cd2bbca490
Create Date: 2025-11-20 17:33:46.192364

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '93e8593d2f8c'
down_revision: Union[str, None] = '62cd2bbca490'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create idea_upvotes table
    op.create_table(
        "idea_upvotes",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("idea_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["idea_id"],
            ["ideas.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "idea_id", name="unique_user_idea_upvote"),
    )
    op.create_index(op.f("ix_idea_upvotes_id"), "idea_upvotes", ["id"], unique=False)
    op.create_index(op.f("ix_idea_upvotes_user_id"), "idea_upvotes", ["user_id"], unique=False)
    op.create_index(op.f("ix_idea_upvotes_idea_id"), "idea_upvotes", ["idea_id"], unique=False)


def downgrade() -> None:
    # Drop idea_upvotes table
    op.drop_index(op.f("ix_idea_upvotes_idea_id"), table_name="idea_upvotes")
    op.drop_index(op.f("ix_idea_upvotes_user_id"), table_name="idea_upvotes")
    op.drop_index(op.f("ix_idea_upvotes_id"), table_name="idea_upvotes")
    op.drop_table("idea_upvotes")

