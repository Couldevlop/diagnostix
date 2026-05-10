"""Endpoints de consultation, téléchargement et envoi des rapports."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, UnauthorizedError
from app.database import get_db
from app.models.report import Report
from app.models.response import DiagnosticSession
from app.schemas.report import ReportOut
from app.services.report_service import verify_signed_url

router = APIRouter()


def _report_to_out(report: Report) -> ReportOut:
    ai = report.ai_analysis or {}
    recos = report.recommendations or []

    risks = []
    if report.status == "READY":
        risks = [
            {
                "id": r.get("code", ""),
                "title": r.get("title", ""),
                "severity": r.get("severity", ""),
                "fcfa_impact": r.get("fcfa_impact", 0),
            }
            for r in (ai.get("risks_detected") or [])
        ]

    return ReportOut(
        report_id=report.id,
        status=report.status,
        global_score=float(report.global_score) if report.status == "READY" else None,
        maturity_level=report.maturity_level if report.status == "READY" else None,
        scores_by_category=(
            {
                "FISCALE": float(report.score_fiscale),
                "SOCIALE": float(report.score_sociale),
                "CONFORMITE": float(report.score_conformite),
                "DIGITALE": float(report.score_digitale),
            }
            if report.status == "READY"
            else None
        ),
        risk_score=float(report.risk_score) if report.status == "READY" else None,
        financial_exposure_fcfa=int(report.financial_exposure) if report.status == "READY" else None,
        turnover_risk_proba=(
            float(report.turnover_risk_proba) if report.status == "READY" else None
        ),
        digital_gap_pct=float(report.digital_gap_pct) if report.status == "READY" else None,
        executive_summary=ai.get("executive_summary") if report.status == "READY" else None,
        risks_detected=risks if report.status == "READY" else None,
        recommendations=(
            [
                {
                    "priority": r.get("priority", 0),
                    "title": r.get("title", ""),
                    "description": r.get("description", ""),
                    "expected_gain_fcfa": r.get("expected_gain_fcfa", 0),
                    "implementation_weeks": r.get("implementation_weeks", 0),
                    "nexusrh_module": r.get("nexusrh_module", ""),
                }
                for r in recos
            ]
            if report.status == "READY"
            else None
        ),
        pdf_url=report.pdf_signed_url,
        generated_at=report.generated_at if report.status == "READY" else None,
    )


@router.get(
    "/{report_id}",
    response_model=ReportOut,
    summary="Récupérer un rapport (JSON) — polling autorisé toutes les 2 s",
)
async def get_report(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise NotFoundError(f"Rapport {report_id} introuvable.")
    return _report_to_out(report)


@router.get(
    "/{report_id}/pdf",
    summary="Télécharger le rapport PDF — token HMAC-SHA256 requis",
)
async def download_report_pdf(
    report_id: uuid.UUID,
    token: str = Query(..., description="Token HMAC-SHA256 signé"),
    expires: int = Query(..., description="Timestamp d'expiration UNIX"),
    db: AsyncSession = Depends(get_db),
) -> Any:
    from app.config import get_settings
    settings = get_settings()

    if not verify_signed_url(
        str(report_id), token, expires,
        settings.pdf_signing_secret.get_secret_value(),
    ):
        raise UnauthorizedError("Token invalide ou expiré.")

    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise NotFoundError(f"Rapport {report_id} introuvable.")
    if report.status != "READY":
        raise NotFoundError("Le rapport n'est pas encore disponible.")
    if not report.pdf_path:
        raise NotFoundError("PDF non encore généré.")

    return FileResponse(
        path=report.pdf_path,
        media_type="application/pdf",
        filename=f"nexus-diagnostix-{report_id}.pdf",
        headers={"Content-Disposition": f'attachment; filename="nexus-diagnostix-{report_id}.pdf"'},
    )


@router.post(
    "/{report_id}/send",
    summary="Envoyer le rapport par email (requiert contact_consent=true sur la session)",
)
async def send_report_email_endpoint(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    from app.config import get_settings
    from app.services.email_service import send_report_email
    from app.services.report_service import MATURITY_LABELS

    settings = get_settings()

    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise NotFoundError(f"Rapport {report_id} introuvable.")
    if report.status != "READY":
        raise NotFoundError("Le rapport n'est pas encore disponible.")

    sess_result = await db.execute(
        select(DiagnosticSession).where(DiagnosticSession.id == report.session_id)
    )
    session = sess_result.scalar_one_or_none()
    if not session or not session.contact_consent or not session.contact_email:
        raise NotFoundError("Aucune adresse email opt-in disponible pour cette session.")

    to_email = session.contact_email
    maturity_label = MATURITY_LABELS.get(str(report.maturity_level), str(report.maturity_level))
    pdf_url = report.pdf_signed_url or ""

    await send_report_email(
        to_email=to_email,
        from_email=settings.email_from,
        global_score=float(report.global_score),
        maturity_level_label=maturity_label,
        pdf_url=pdf_url,
        sendgrid_api_key=(
            settings.sendgrid_api_key.get_secret_value()
            if settings.email_provider == "sendgrid"
            else None
        ),
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_username=settings.smtp_user or None,
        smtp_password=(
            settings.smtp_password.get_secret_value()
            if settings.smtp_password.get_secret_value()
            else None
        ),
    )

    from datetime import datetime, timezone
    report.sent_to_email = True
    report.sent_at = datetime.now(timezone.utc)
    await db.commit()

    return {"sent": True, "to": to_email}
