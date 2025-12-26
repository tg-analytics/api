from collections.abc import Sequence
from typing import Union

from alembic import op
import sqlalchemy as sa


revision: str = "20240717_000002"
down_revision: Union[str, None] = "20240101_000001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


team_member_status = sa.Enum("invited", "accepted", "rejected", name="team_member_status")


def upgrade() -> None:
    team_member_status.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "team_members",
        sa.Column(
            "status",
            team_member_status,
            nullable=False,
            server_default="accepted",
        ),
    )
    op.execute("UPDATE team_members SET status = 'accepted' WHERE status IS NULL")
    op.alter_column("team_members", "status", server_default="accepted", nullable=False)


def downgrade() -> None:
    op.drop_column("team_members", "status")
    team_member_status.drop(op.get_bind(), checkfirst=True)
