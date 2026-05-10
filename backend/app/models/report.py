"""Modèle Report — rapport de diagnostic généré."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Report(Base):
    """Rapport de diagnostic finalisé.

    Toutes les métriques numériques sont stockées telles que calculées par les
    moteurs déterministes ; le champ JSONB `ai_analysis` contient le payload
    structuré renvoyé par Claude (validé par Pydantic avant insertion).
    """

    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="GENERATING"
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("diagnostic_sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # --- Scores ---
    global_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    score_fiscale: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    score_sociale: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    score_conformite: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    score_digitale: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    maturity_level: Mapped[str] = mapped_column(String(20), nullable=False)

    # --- Risques ---
    risk_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    financial_exposure: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    turnover_risk_proba: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    digital_gap_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    # --- IA ---
    ai_analysis: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    recommendations: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)

    # --- PDF ---
    pdf_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    pdf_signed_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    pdf_url_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # --- Distribution ---
    sent_to_email: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<Report {self.id} score={self.global_score} level={self.maturity_level}>"
