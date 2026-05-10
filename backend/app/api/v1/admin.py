"""Endpoints d'administration (questions, settings, statistiques, leads, audit)."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from jose import JWTError
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.question import Question
from app.models.report import Report
from app.models.response import DiagnosticSession
from app.models.setting import Setting

router = APIRouter()


# ---------------------------------------------------------------------------
# Dépendance auth JWT
# ---------------------------------------------------------------------------
async def require_admin(authorization: str = Header(...)) -> dict[str, Any]:
    """Vérifie le JWT Bearer et retourne le payload."""
    if not authorization.startswith("Bearer "):
        raise UnauthorizedError("Token Bearer manquant.")
    token = authorization.removeprefix("Bearer ")
    settings = get_settings()
    try:
        payload = decode_access_token(
            token,
            settings.secret_key.get_secret_value(),
            settings.jwt_algorithm,
        )
    except JWTError:
        raise UnauthorizedError("Token invalide ou expiré.")
    return payload


# ---------------------------------------------------------------------------
# Questions
# ---------------------------------------------------------------------------
class QuestionUpdateIn(BaseModel):
    label: str | None = None
    weight: int | None = None
    help_text: str | None = None
    order: int | None = None


@router.get("/questions", summary="Lister les questions")
async def list_admin_questions(
    db: AsyncSession = Depends(get_db),
    _: Any = Depends(require_admin),
) -> Any:
    result = await db.execute(select(Question).order_by(Question.order))
    questions = result.scalars().all()
    return {"questions": [
        {
            "id": q.id, "code": q.code, "label": q.label,
            "category": q.category, "weight": q.weight,
            "answer_type": q.answer_type, "order": q.order,
            "is_active": q.is_active, "help_text": q.help_text,
        }
        for q in questions
    ]}


@router.put("/questions/{question_id}", summary="Modifier une question")
async def update_question(
    question_id: int,
    body: QuestionUpdateIn,
    db: AsyncSession = Depends(get_db),
    _: Any = Depends(require_admin),
) -> Any:
    result = await db.execute(select(Question).where(Question.id == question_id))
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question introuvable.")
    if body.label is not None:
        question.label = body.label
    if body.weight is not None:
        question.weight = body.weight
    if body.help_text is not None:
        question.help_text = body.help_text
    if body.order is not None:
        question.order = body.order
    await db.commit()
    return {"updated": True, "id": question_id}


@router.patch("/questions/{question_id}/toggle", summary="Activer/désactiver une question")
async def toggle_question(
    question_id: int,
    db: AsyncSession = Depends(get_db),
    _: Any = Depends(require_admin),
) -> Any:
    result = await db.execute(select(Question).where(Question.id == question_id))
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question introuvable.")
    question.is_active = not question.is_active
    await db.commit()
    return {"id": question_id, "is_active": question.is_active}


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
class SettingUpdateIn(BaseModel):
    value: Any


@router.get("/settings", summary="Récupérer tous les paramètres")
async def list_settings(
    db: AsyncSession = Depends(get_db),
    _: Any = Depends(require_admin),
) -> Any:
    result = await db.execute(select(Setting))
    settings = result.scalars().all()
    return {"settings": [{"key": s.key, "value": s.value, "description": s.description} for s in settings]}


@router.put("/settings/{key}", summary="Modifier un paramètre")
async def update_setting(
    key: str,
    body: SettingUpdateIn,
    db: AsyncSession = Depends(get_db),
    payload: Any = Depends(require_admin),
) -> Any:
    result = await db.execute(select(Setting).where(Setting.key == key))
    setting = result.scalar_one_or_none()
    if not setting:
        raise HTTPException(status_code=404, detail="Paramètre introuvable.")
    setting.value = body.value
    setting.updated_by = int(payload.get("sub", 0)) or None
    await db.commit()
    return {"updated": True, "key": key}


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------
@router.get("/stats", summary="KPIs agrégés")
async def admin_stats(
    db: AsyncSession = Depends(get_db),
    _: Any = Depends(require_admin),
) -> Any:
    total_sessions = await db.scalar(select(func.count()).select_from(DiagnosticSession)) or 0
    completed = await db.scalar(
        select(func.count()).select_from(DiagnosticSession).where(DiagnosticSession.status == "COMPLETED")
    ) or 0
    avg_score = await db.scalar(
        select(func.avg(Report.global_score)).select_from(Report).where(Report.status == "READY")
    )
    return {
        "total_sessions": total_sessions,
        "completed_sessions": completed,
        "completion_rate": round(completed / total_sessions * 100, 1) if total_sessions else 0.0,
        "average_global_score": round(float(avg_score), 2) if avg_score else None,
    }


# ---------------------------------------------------------------------------
# Leads (emails opt-in)
# ---------------------------------------------------------------------------
@router.get("/leads", summary="Emails opt-in (données ARTCI)")
async def list_leads(
    db: AsyncSession = Depends(get_db),
    _: Any = Depends(require_admin),
) -> Any:
    result = await db.execute(
        select(DiagnosticSession)
        .where(DiagnosticSession.contact_consent == True)  # noqa: E712
        .where(DiagnosticSession.contact_email.is_not(None))
        .order_by(DiagnosticSession.started_at.desc())
    )
    sessions = result.scalars().all()
    return {"leads": [
        {
            "session_id": str(s.id),
            "contact_email": s.contact_email,
            "sector": s.sector,
            "company_size": s.company_size,
            "started_at": s.started_at.isoformat() if s.started_at else None,
        }
        for s in sessions
    ]}


# ---------------------------------------------------------------------------
# Audit logs
# ---------------------------------------------------------------------------
@router.get("/audit-logs", summary="Journal d'audit (50 dernières entrées)")
async def list_audit_logs(
    db: AsyncSession = Depends(get_db),
    _: Any = Depends(require_admin),
    limit: int = Query(default=50, ge=1, le=500),
) -> Any:
    result = await db.execute(
        select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    )
    logs = result.scalars().all()
    return {"audit_logs": [
        {
            "id": log.id,
            "actor_type": log.actor_type,
            "actor_id": log.actor_id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]}
