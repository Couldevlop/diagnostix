"""Endpoints d'administration (questions, settings, statistiques)."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get(
    "/questions",
    summary="Lister les questions (admin)",
)
async def list_admin_questions() -> dict[str, str]:
    """Endpoint à implémenter au Sprint 9."""
    return {"status": "not_implemented", "sprint": "9"}


@router.get(
    "/stats",
    summary="KPIs agrégés (sessions, scores moyens, distribution maturité)",
)
async def admin_stats() -> dict[str, str]:
    """Endpoint à implémenter au Sprint 9."""
    return {"status": "not_implemented", "sprint": "9"}


@router.get(
    "/settings",
    summary="Récupérer les paramètres applicatifs (taux fiscaux, etc.)",
)
async def list_settings() -> dict[str, str]:
    """Endpoint à implémenter au Sprint 9."""
    return {"status": "not_implemented", "sprint": "9"}
