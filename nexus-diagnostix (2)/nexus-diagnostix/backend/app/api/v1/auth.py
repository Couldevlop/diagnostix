"""Endpoints d'authentification administrateur."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.post(
    "/login",
    summary="Connexion admin (email + mot de passe → JWT)",
)
async def login() -> dict[str, str]:
    """Endpoint à implémenter au Sprint 9."""
    return {"status": "not_implemented", "sprint": "9"}


@router.post(
    "/refresh",
    summary="Rafraîchir un token JWT",
)
async def refresh_token() -> dict[str, str]:
    """Endpoint à implémenter au Sprint 9."""
    return {"status": "not_implemented", "sprint": "9"}
