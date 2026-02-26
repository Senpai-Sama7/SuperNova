"""audit_logs table

Revision ID: b7c3e9f12a45
Revises: 23aa65fd8071
Create Date: 2026-02-26 14:30:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b7c3e9f12a45"
down_revision: str | Sequence[str] | None = "23aa65fd8071"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "supernova_audit_logs",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("user_id", sa.Text, nullable=False),
        sa.Column("action", sa.Text, nullable=False),
        sa.Column("resource", sa.Text, nullable=True),
        sa.Column("details", sa.JSON, nullable=True),
        sa.Column("ip_address", sa.Text, nullable=True),
    )
    op.create_index("ix_sn_audit_logs_timestamp", "supernova_audit_logs", ["timestamp"])
    op.create_index("ix_sn_audit_logs_user_id", "supernova_audit_logs", ["user_id"])
    op.create_index("ix_sn_audit_logs_action", "supernova_audit_logs", ["action"])


def downgrade() -> None:
    op.drop_table("supernova_audit_logs")
