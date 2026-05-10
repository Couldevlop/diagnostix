"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-05-07 10:00:00.000000
"""
from __future__ import annotations

from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- questions -----------------------------------------------------------
    op.create_table(
        "questions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(10), nullable=False, unique=True),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("category", sa.String(20), nullable=False),
        sa.Column("weight", sa.Integer(), nullable=False),
        sa.Column("answer_type", sa.String(20), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("help_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "category IN ('FISCALE','SOCIALE','CONFORMITE','DIGITALE')",
            name="ck_question_category",
        ),
        sa.CheckConstraint("weight BETWEEN 1 AND 20", name="ck_question_weight"),
        sa.CheckConstraint(
            "answer_type IN ('YES_NO','YES_NO_PARTIAL','YES_NO_MANUAL','FREE_NUMERIC')",
            name="ck_question_answer_type",
        ),
    )

    # --- diagnostic_sessions -------------------------------------------------
    op.create_table(
        "diagnostic_sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("company_size", sa.String(20), nullable=True),
        sa.Column("sector", sa.String(50), nullable=True),
        sa.Column("contact_email", sa.String(512), nullable=True),
        sa.Column("contact_consent", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("ip_hash", sa.String(64), nullable=False),
        sa.Column("user_agent_hash", sa.String(64), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="IN_PROGRESS"),
        sa.CheckConstraint(
            "status IN ('IN_PROGRESS','COMPLETED','ABANDONED')",
            name="ck_session_status",
        ),
    )
    op.create_index("idx_sessions_status", "diagnostic_sessions", ["status"])
    op.create_index("idx_sessions_completed", "diagnostic_sessions", ["completed_at"])

    # --- responses -----------------------------------------------------------
    op.create_table(
        "responses",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("diagnostic_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "question_id",
            sa.Integer(),
            sa.ForeignKey("questions.id"),
            nullable=False,
        ),
        sa.Column("answer_value", sa.String(50), nullable=False),
        sa.Column("answer_numeric", sa.Numeric(), nullable=True),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("session_id", "question_id", name="uq_response_session_question"),
    )

    # --- users ---------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="ADMIN"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("role IN ('ADMIN','SUPERADMIN')", name="ck_user_role"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # --- reports -------------------------------------------------------------
    op.create_table(
        "reports",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("diagnostic_sessions.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("global_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("score_fiscale", sa.Numeric(5, 2), nullable=False),
        sa.Column("score_sociale", sa.Numeric(5, 2), nullable=False),
        sa.Column("score_conformite", sa.Numeric(5, 2), nullable=False),
        sa.Column("score_digitale", sa.Numeric(5, 2), nullable=False),
        sa.Column("maturity_level", sa.String(20), nullable=False),
        sa.Column("risk_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("financial_exposure", sa.Numeric(15, 2), nullable=False),
        sa.Column("turnover_risk_proba", sa.Numeric(4, 3), nullable=False),
        sa.Column("digital_gap_pct", sa.Numeric(5, 2), nullable=False),
        sa.Column("ai_analysis", postgresql.JSONB(), nullable=False),
        sa.Column("recommendations", postgresql.JSONB(), nullable=False),
        sa.Column("pdf_path", sa.String(500), nullable=True),
        sa.Column("pdf_signed_url", sa.Text(), nullable=True),
        sa.Column("pdf_url_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_to_email", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # --- settings ------------------------------------------------------------
    op.create_table(
        "settings",
        sa.Column("key", sa.String(50), primary_key=True),
        sa.Column("value", postgresql.JSONB(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("updated_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # --- audit_logs ----------------------------------------------------------
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("actor_type", sa.String(20), nullable=False),
        sa.Column("actor_id", sa.String(64), nullable=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=True),
        sa.Column("resource_id", sa.String(64), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=True),
        sa.Column("ip_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_audit_created", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("idx_audit_created", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_table("settings")
    op.drop_table("reports")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    op.drop_table("responses")
    op.drop_index("idx_sessions_completed", table_name="diagnostic_sessions")
    op.drop_index("idx_sessions_status", table_name="diagnostic_sessions")
    op.drop_table("diagnostic_sessions")
    op.drop_table("questions")
