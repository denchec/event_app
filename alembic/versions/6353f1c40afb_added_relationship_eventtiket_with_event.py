"""added relationship EventTiket with Event

Revision ID: 6353f1c40afb
Revises: 295a733d6a77
Create Date: 2026-05-13 18:17:14.824367

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6353f1c40afb"
down_revision: Union[str, Sequence[str], None] = "295a733d6a77"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("event_tickets"):
        columns = {column["name"] for column in inspector.get_columns("event_tickets")}
        if "event_id" in columns:
            op.drop_column("event_tickets", "event_id")


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("event_tickets"):
        columns = {column["name"] for column in inspector.get_columns("event_tickets")}
        if "event_id" not in columns:
            op.add_column(
                "event_tickets",
                sa.Column(
                    "event_id", sa.VARCHAR(length=36), autoincrement=False, nullable=False
                ),
            )
