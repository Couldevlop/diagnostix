"""add status column to reports

Revision ID: 0002_add_reports_status
Revises: 0001_initial_schema
Create Date: 2026-05-08 19:00:00.000000
"""
from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_add_reports_status"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "reports",
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="READY",
        ),
    )


def downgrade() -> None:
    op.drop_column("reports", "status")
