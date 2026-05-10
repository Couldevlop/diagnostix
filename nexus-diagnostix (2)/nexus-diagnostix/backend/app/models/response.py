"""Modèles `DiagnosticSession` et `Response`."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SessionStatus(StrEnum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"


class DiagnosticSession(Base):
    """Une session de diagnostic anonyme (1 visiteur = 1 session)."""

    __tablename__ = "diagnostic_sessions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('IN_PROGRESS','COMPLETED','ABANDONED')",
            name="ck_session_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_size: Mapped[str | None] = mapped_column(String(20), nullable=True)
    sector: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # Email chiffré applicativement (Fernet) avant stockage
    contact_email: Mapped[str | None] = mapped_column(String(512), nullable=True)
    contact_consent: Mapped[bool] = mapped_column(default=False, nullable=False)
    ip_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    user_agent_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=SessionStatus.IN_PROGRESS.value
    )

    responses: Mapped[list[Response]] = relationship(
        "Response", back_populates="session", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<DiagnosticSession {self.id} status={self.status}>"


class Response(Base):
    """Réponse d'un visiteur à une question."""

    __tablename__ = "responses"
    __table_args__ = (
        UniqueConstraint("session_id", "question_id", name="uq_response_session_question"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("diagnostic_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("questions.id"), nullable=False
    )
    answer_value: Mapped[str] = mapped_column(String(50), nullable=False)
    answer_numeric: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    answered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    session: Mapped[DiagnosticSession] = relationship(
        "DiagnosticSession", back_populates="responses"
    )

    def __repr__(self) -> str:
        return f"<Response session={self.session_id} q={self.question_id} = {self.answer_value}>"
