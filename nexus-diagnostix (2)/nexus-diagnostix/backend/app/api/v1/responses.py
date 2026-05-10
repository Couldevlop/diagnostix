"""Endpoints d'enregistrement des réponses individuelles."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

router = APIRouter()


@router.post(
    "/{session_id}/responses",
    summary="Enregistrer la réponse à une question (idempotent)",
)
async def save_response(session_id: UUID) -> dict[str, str]:
    """Endpoint à implémenter au Sprint 6."""
    return {"status": "not_implemented", "sprint": "6", "session_id": str(session_id)}
