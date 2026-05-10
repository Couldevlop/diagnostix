"""Schémas Pydantic pour les questions et sessions."""
from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class SessionCreateIn(BaseModel):
    company_size: str | None = None
    sector: str | None = None
    contact_email: EmailStr | None = None
    contact_consent: bool = False


class SessionCreateOut(BaseModel):
    session_id: uuid.UUID
    started_at: Any
    total_questions: int


class QuestionOut(BaseModel):
    id: int
    code: str
    label: str
    category: str
    answer_type: str
    order: int
    help_text: str | None

    model_config = {"from_attributes": True}


class QuestionsListOut(BaseModel):
    questions: list[QuestionOut]


class FinalizeOut(BaseModel):
    report_id: uuid.UUID
    status: str
    estimated_seconds: int = 15
