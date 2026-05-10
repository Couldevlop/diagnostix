"""Endpoints sessions (création, liste questions, finalisation)."""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.database import get_db
from app.models.question import Question
from app.models.report import Report
from app.models.response import DiagnosticSession, Response, SessionStatus
from app.schemas.question import (
    FinalizeOut,
    QuestionsListOut,
    QuestionOut,
    SessionCreateIn,
    SessionCreateOut,
)
from app.services.ml_engine import MLInput, run_predictions
from app.services.risk_engine import RiskContext, compute_risks
from app.services.scoring_engine import QuestionMeta, ResponseInput, compute_scores
from app.services.ai_service import get_ai_analysis

router = APIRouter()


def _hash_ip(ip: str) -> str:
    return hashlib.sha256(ip.encode()).hexdigest()


async def _generate_report(
    session_id: uuid.UUID,
    report_id: uuid.UUID,
    db_session: AsyncSession,
) -> None:
    """Pipeline de génération du rapport (exécuté en background)."""
    try:
        # Charger la session et ses réponses
        sess_result = await db_session.execute(
            select(DiagnosticSession).where(DiagnosticSession.id == session_id)
        )
        diag_session = sess_result.scalar_one_or_none()
        if not diag_session:
            return

        resp_result = await db_session.execute(
            select(Response).where(Response.session_id == session_id)
        )
        responses = list(resp_result.scalars().all())

        # Charger les questions actives
        q_result = await db_session.execute(
            select(Question).where(Question.is_active == True).order_by(Question.order)  # noqa: E712
        )
        questions = list(q_result.scalars().all())

        # Étage 1 — Scoring
        q_meta = [QuestionMeta(q.code, q.category, q.weight, q.answer_type) for q in questions]
        r_inputs = [
            ResponseInput(
                question_code=next(
                    (qq.code for qq in questions if qq.id == r.question_id), ""
                ),
                answer_value=r.answer_value,
                answer_numeric=float(r.answer_numeric) if r.answer_numeric is not None else None,
            )
            for r in responses
        ]
        score_result = compute_scores(q_meta, r_inputs)

        # Étage 2 — Risk Engine
        resp_by_code = {ri.question_code: ri.answer_value for ri in r_inputs}
        effectif = 10  # défaut conservateur
        risk_result = compute_risks(RiskContext(responses_by_code=resp_by_code, effectif=effectif))

        # Étage 3 — ML
        ml_input = MLInput(
            responses_by_code=resp_by_code,
            score_fiscale=score_result.score_fiscale,
            score_sociale=score_result.score_sociale,
            company_size=diag_session.company_size or "11-50",
        )
        ml_pred = run_predictions(ml_input)

        # Étage 4 — Claude AI
        risks_for_ai = [
            {"code": r.code, "title": r.title, "severity": r.severity, "fcfa_impact": r.fcfa_impact}
            for r in risk_result.detected_risks
        ]
        ai_analysis = get_ai_analysis(
            global_score=score_result.global_score,
            maturity_level=score_result.maturity_level,
            scores_by_category=score_result.scores_by_category,
            risks_detected=risks_for_ai,
            financial_exposure=risk_result.financial_exposure,
            non_compliance_proba=ml_pred.non_compliance_proba,
            digital_gap_pct=score_result.digital_gap_pct,
        )

        # Mise à jour du rapport
        report_result = await db_session.execute(
            select(Report).where(Report.id == report_id)
        )
        report = report_result.scalar_one_or_none()
        if not report:
            return

        report.status = "READY"
        report.global_score = score_result.global_score  # type: ignore[assignment]
        report.score_fiscale = score_result.score_fiscale  # type: ignore[assignment]
        report.score_sociale = score_result.score_sociale  # type: ignore[assignment]
        report.score_conformite = score_result.score_conformite  # type: ignore[assignment]
        report.score_digitale = score_result.score_digitale  # type: ignore[assignment]
        report.maturity_level = score_result.maturity_level
        report.risk_score = risk_result.risk_score  # type: ignore[assignment]
        report.financial_exposure = risk_result.financial_exposure  # type: ignore[assignment]
        report.turnover_risk_proba = ml_pred.turnover_risk_proba or 0.0  # type: ignore[assignment]
        report.digital_gap_pct = score_result.digital_gap_pct  # type: ignore[assignment]
        report.ai_analysis = ai_analysis.model_dump()
        report.recommendations = [r.model_dump() for r in ai_analysis.recommendations]
        report.generated_at = datetime.now(timezone.utc)

        await db_session.commit()

    except Exception:  # noqa: BLE001
        # En cas d'échec, marquer le rapport comme FAILED
        try:
            report_result = await db_session.execute(
                select(Report).where(Report.id == report_id)
            )
            report = report_result.scalar_one_or_none()
            if report:
                report.status = "FAILED"
                await db_session.commit()
        except Exception:  # noqa: BLE001
            pass


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=SessionCreateOut,
    summary="Démarrer une nouvelle session de diagnostic",
)
async def create_session(
    body: SessionCreateIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Crée une session anonyme. L'email est chiffré si opt-in (§11.1 ARTCI)."""
    ip = request.client.host if request.client else "unknown"
    session = DiagnosticSession(
        id=uuid.uuid4(),
        company_size=body.company_size,
        sector=body.sector,
        contact_email=body.contact_email if body.contact_consent else None,
        contact_consent=body.contact_consent,
        ip_hash=_hash_ip(ip),
        status=SessionStatus.IN_PROGRESS.value,
    )
    db.add(session)
    await db.flush()

    total_q = await db.scalar(
        select(func.count()).where(Question.is_active == True)  # noqa: E712
    )
    return {"session_id": session.id, "started_at": session.started_at, "total_questions": total_q or 20}


@router.get(
    "/{session_id}/questions",
    response_model=QuestionsListOut,
    summary="Récupérer la liste ordonnée des questions actives",
)
async def list_questions(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    result = await db.execute(
        select(DiagnosticSession).where(DiagnosticSession.id == session_id)
    )
    if not result.scalar_one_or_none():
        raise NotFoundError(f"Session {session_id} introuvable.")

    q_result = await db.execute(
        select(Question).where(Question.is_active == True).order_by(Question.order)  # noqa: E712
    )
    questions = q_result.scalars().all()
    return {"questions": [QuestionOut.model_validate(q) for q in questions]}


@router.post(
    "/{session_id}/finalize",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=FinalizeOut,
    summary="Verrouiller la session et déclencher la génération du rapport",
)
async def finalize_session(
    session_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Finalise la session et démarre la génération du rapport en background."""
    sess_result = await db.execute(
        select(DiagnosticSession).where(DiagnosticSession.id == session_id)
    )
    session = sess_result.scalar_one_or_none()
    if not session:
        raise NotFoundError(f"Session {session_id} introuvable.")
    if session.status == SessionStatus.COMPLETED.value:
        # Idempotent : retourner le rapport existant (React StrictMode double-appel)
        existing_report = await db.scalar(
            select(Report).where(Report.session_id == session_id)
        )
        if existing_report:
            return {"report_id": existing_report.id, "status": existing_report.status, "estimated_seconds": 0}
        raise ConflictError("Session déjà finalisée.")

    # Vérifier qu'il y a au moins une réponse
    resp_count = await db.scalar(
        select(func.count()).where(Response.session_id == session_id)
    )
    if not resp_count:
        raise ValidationError("Aucune réponse enregistrée — impossible de finaliser.")

    # Verrouiller la session
    session.status = SessionStatus.COMPLETED.value
    session.completed_at = datetime.now(timezone.utc)

    # Créer le rapport (statut initial = GENERATING)
    # Valeurs placeholder jusqu'à ce que le background task les remplisse
    report = Report(
        id=uuid.uuid4(),
        session_id=session_id,
        status="GENERATING",
        global_score=0,
        score_fiscale=0,
        score_sociale=0,
        score_conformite=0,
        score_digitale=0,
        maturity_level="CRITIQUE",
        risk_score=0,
        financial_exposure=0,
        turnover_risk_proba=0,
        digital_gap_pct=0,
        ai_analysis={},
        recommendations=[],
    )
    db.add(report)
    await db.flush()
    report_id = report.id
    await db.commit()

    # Lancer la génération en arrière-plan
    from app.database import AsyncSessionLocal
    async def bg_generate() -> None:
        async with AsyncSessionLocal() as bg_db:
            await _generate_report(session_id, report_id, bg_db)

    background_tasks.add_task(bg_generate)

    return {"report_id": report_id, "status": "GENERATING", "estimated_seconds": 15}
