"""Extend notification_type enum with invite_accepted

Revision ID: 20241102_000003
Revises: 20240717_000002
Create Date: 2024-11-02 00:00:00
"""
from collections.abc import Sequence
from typing import Union

from alembic import op

revision: str = "20241102_000003"
down_revision: Union[str, None] = "20240717_000002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


notification_type_new_value = "invite_accepted"
notification_type_enum_name = "notification_type"

def upgrade() -> None:
    op.execute(
        f"ALTER TYPE {notification_type_enum_name} ADD VALUE IF NOT EXISTS '{notification_type_new_value}'"
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            -- Create a new enum type without the removed value
            CREATE TYPE notification_type_old AS ENUM ('welcome', 'news', 'updates');

            -- Change columns to use the temporary type
            ALTER TABLE notifications ALTER COLUMN type TYPE notification_type_old USING type::text::notification_type_old;

            -- Drop the new type and rename the old one back
            DROP TYPE notification_type;
            ALTER TYPE notification_type_old RENAME TO notification_type;
        END;
        $$;
        """
    )
