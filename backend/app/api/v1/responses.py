"""Endpoints d'enregistrement des réponses individuelles."""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.database import get_db
from app.models.question import Question
from app.models.response import DiagnosticSession, Response, SessionStatus
from app.schemas.response import ResponseIn, ResponseSavedOut

router = APIRouter()


@router.post(
    "/{session_id}/responses",
    response_model=ResponseSavedOut,
    summary="Enregistrer la réponse à une question (idempotent par session+question)",
)
async def save_response(
    session_id: uuid.UUID,
    body: ResponseIn,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Enregistre ou met à jour la réponse. Idempotent : un second appel avec
    la même question remplace la valeur précédente sans créer de doublon."""
    # Vérifier que la session existe et est toujours ouverte
    sess_result = await db.execute(
        select(DiagnosticSession).where(DiagnosticSession.id == session_id)
    )
    session = sess_result.scalar_one_or_none()
    if not session:
        raise NotFoundError(f"Session {session_id} introuvable.")
    if session.status == SessionStatus.COMPLETED.value:
        raise ConflictError("Session déjà finalisée — aucune modification possible.")

    # Vérifier que la question existe
    q_result = await db.execute(
        select(Question).where(Question.id == body.question_id, Question.is_active == True)  # noqa: E712
    )
    if not q_result.scalar_one_or_none():
        raise NotFoundError(f"Question {body.question_id} introuvable ou inactive.")

    # Upsert idempotent
    existing_result = await db.execute(
        select(Response).where(
            Response.session_id == session_id,
            Response.question_id == body.question_id,
        )
    )
    existing = existing_result.scalar_one_or_none()
    if existing:
        existing.answer_value = body.answer_value
        existing.answer_numeric = body.answer_numeric  # type: ignore[assignment]
    else:
        db.add(Response(
            session_id=session_id,
            question_id=body.question_id,
            answer_value=body.answer_value,
            answer_numeric=body.answer_numeric,  # type: ignore[arg-type]
        ))
    await db.flush()

    # Calculer la progression
    total = await db.scalar(
        select(func.count()).where(Question.is_active == True)  # noqa: E712
    ) or 0
    answered = await db.scalar(
        select(func.count()).where(Response.session_id == session_id)
    ) or 0

    return {
        "saved": True,
        "progress": {
            "answered": answered,
            "total": total,
            "percent": round(answered / total * 100, 1) if total else 0.0,
        },
    }
