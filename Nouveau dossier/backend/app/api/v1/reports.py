"""Endpoints de consultation et de téléchargement des rapports."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

router = APIRouter()


@router.get(
    "/{report_id}",
    summary="Récupérer un rapport (JSON)",
)
async def get_report(report_id: UUID) -> dict[str, str]:
    """Endpoint à implémenter au Sprint 7."""
    return {"status": "not_implemented", "sprint": "7", "report_id": str(report_id)}


@router.get(
    "/{report_id}/pdf",
    summary="Télécharger le rapport au format PDF",
)
async def download_report_pdf(report_id: UUID) -> dict[str, str]:
    """Endpoint à implémenter au Sprint 7."""
    return {"status": "not_implemented", "sprint": "7", "report_id": str(report_id)}


@router.post(
    "/{report_id}/send",
    summary="Envoyer le rapport par email",
)
async def send_report_email(report_id: UUID) -> dict[str, str]:
    """Endpoint à implémenter au Sprint 8."""
    return {"status": "not_implemented", "sprint": "8", "report_id": str(report_id)}
