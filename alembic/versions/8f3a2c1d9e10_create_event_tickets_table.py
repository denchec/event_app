"""create event_tickets table

Revision ID: 8f3a2c1d9e10
Revises: 6353f1c40afb
Create Date: 2026-05-14 15:25:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8f3a2c1d9e10"
down_revision: Union[str, Sequence[str], None] = "6353f1c40afb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("event_tickets"):
        op.create_table(
            "event_tickets",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("event_id", sa.String(length=36), nullable=False),
            sa.ForeignKeyConstraint(["event_id"], ["events.id"]),
            sa.PrimaryKeyConstraint("id"),
        )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("event_tickets"):
        op.drop_table("event_tickets")
