"""Endpoints liés aux sessions de diagnostic et au questionnaire."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, status

router = APIRouter()


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Démarrer une nouvelle session de diagnostic",
    description=(
        "Crée une session anonyme de diagnostic. L'email est optionnel et ne "
        "sera stocké (chiffré) que si `contact_consent` est `true`, "
        "conformément à la Loi ARTCI n°2013-450."
    ),
)
async def create_session() -> dict[str, str]:
    """Endpoint à implémenter au Sprint 6.

    Sera couvert à 100 % par les tests d'intégration.
    """
    return {"status": "not_implemented", "sprint": "6"}


@router.get(
    "/{session_id}/questions",
    summary="Récupérer la liste ordonnée des questions actives",
)
async def list_questions(session_id: UUID) -> dict[str, str]:
    """Endpoint à implémenter au Sprint 6."""
    return {"status": "not_implemented", "sprint": "6", "session_id": str(session_id)}


@router.post(
    "/{session_id}/finalize",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Verrouiller la session et déclencher la génération du rapport",
)
async def finalize_session(session_id: UUID) -> dict[str, str]:
    """Endpoint à implémenter au Sprint 6."""
    return {"status": "not_implemented", "sprint": "6", "session_id": str(session_id)}
