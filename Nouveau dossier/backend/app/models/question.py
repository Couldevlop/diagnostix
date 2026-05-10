"""Modèle Question — les 20 questions du diagnostic, gérées par l'admin."""
from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class QuestionCategory(StrEnum):
    """Catégories des questions, reprises du cahier des charges."""

    FISCALE = "FISCALE"
    SOCIALE = "SOCIALE"
    CONFORMITE = "CONFORMITE"
    DIGITALE = "DIGITALE"


class AnswerType(StrEnum):
    """Types de réponses possibles."""

    YES_NO = "YES_NO"
    YES_NO_PARTIAL = "YES_NO_PARTIAL"
    YES_NO_MANUAL = "YES_NO_MANUAL"
    FREE_NUMERIC = "FREE_NUMERIC"


class Question(Base):
    """Une question du questionnaire de diagnostic."""

    __tablename__ = "questions"
    __table_args__ = (
        CheckConstraint(
            "category IN ('FISCALE','SOCIALE','CONFORMITE','DIGITALE')",
            name="ck_question_category",
        ),
        CheckConstraint("weight BETWEEN 1 AND 20", name="ck_question_weight"),
        CheckConstraint(
            "answer_type IN ('YES_NO','YES_NO_PARTIAL','YES_NO_MANUAL','FREE_NUMERIC')",
            name="ck_question_answer_type",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    weight: Mapped[int] = mapped_column(Integer, nullable=False)
    answer_type: Mapped[str] = mapped_column(String(20), nullable=False)
    order: Mapped[int] = mapped_column("order", Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    help_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<Question {self.code} '{self.label[:40]}…' weight={self.weight}>"
