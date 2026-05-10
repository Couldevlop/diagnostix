"""Endpoints d'authentification administrateur."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import (
    create_access_token,
    decode_access_token,
    verify_password,
)
from app.database import get_db
from app.models.user import User
from app.schemas.report import AuthTokenOut

router = APIRouter()

# Nombre maximum de tentatives avant verrouillage du compte
MAX_FAILED_ATTEMPTS = 5


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class RefreshIn(BaseModel):
    refresh_token: str


@router.post(
    "/login",
    response_model=AuthTokenOut,
    status_code=status.HTTP_200_OK,
    summary="Connexion admin (email + mot de passe → JWT 8 h)",
)
async def login(body: LoginIn, db: AsyncSession = Depends(get_db)) -> Any:
    """Authentifie un admin et retourne un JWT.

    Bruteforce protection : compte verrouillé après 5 tentatives (§11.2).
    """
    settings = get_settings()

    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    # Compte introuvable ou inactif
    if not user or not user.is_active:
        raise UnauthorizedError("Identifiants incorrects.")

    # Compte verrouillé (locked_until peut être naive si SQLite)
    now_utc = datetime.now(timezone.utc)
    locked = user.locked_until
    if locked:
        if locked.tzinfo is None:
            locked = locked.replace(tzinfo=timezone.utc)
    if locked and locked > now_utc:
        raise ForbiddenError("Compte temporairement verrouillé. Réessayez dans 15 minutes.")

    # Vérification du mot de passe
    if not verify_password(body.password, user.password_hash):
        user.failed_attempts += 1
        if user.failed_attempts >= MAX_FAILED_ATTEMPTS:
            from datetime import timedelta
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
        await db.commit()
        raise UnauthorizedError("Identifiants incorrects.")

    # Réinitialisation des compteurs d'échec
    user.failed_attempts = 0
    user.locked_until = None
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    token = create_access_token(
        data={"sub": str(user.id), "role": user.role, "email": user.email},
        secret=settings.secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
        expires_minutes=settings.jwt_access_token_expire_minutes,
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.jwt_access_token_expire_minutes * 60,
    }


@router.post(
    "/refresh",
    response_model=AuthTokenOut,
    summary="Rafraîchir un token JWT",
)
async def refresh_token(body: RefreshIn, db: AsyncSession = Depends(get_db)) -> Any:
    """Génère un nouveau JWT à partir d'un token existant encore valide."""
    from jose import JWTError
    settings = get_settings()
    try:
        payload = decode_access_token(
            body.refresh_token,
            settings.secret_key.get_secret_value(),
            settings.jwt_algorithm,
        )
    except JWTError:
        raise UnauthorizedError("Token invalide ou expiré.")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise UnauthorizedError("Utilisateur introuvable ou inactif.")

    token = create_access_token(
        data={"sub": str(user.id), "role": user.role, "email": user.email},
        secret=settings.secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
        expires_minutes=settings.jwt_access_token_expire_minutes,
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.jwt_access_token_expire_minutes * 60,
    }
