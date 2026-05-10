"""Réinitialise le mot de passe de l'admin initial.

Usage :
    docker compose exec backend python -m app.scripts.reset_admin_password
"""
from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.config import get_settings
from app.core.security import hash_password
from app.database import AsyncSessionLocal
from app.models.user import User


async def reset() -> None:
    settings = get_settings()
    email = settings.initial_admin_email
    plain = settings.initial_admin_password.get_secret_value()

    if not plain:
        print("❌  INITIAL_ADMIN_PASSWORD est vide dans .env — définissez-le d'abord.")
        return

    async with AsyncSessionLocal() as session:
        async with session.begin():
            result = await session.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()

            if user is None:
                print(f"❌  Aucun utilisateur trouvé avec l'email : {email}")
                return

            user.password_hash = hash_password(plain)
            user.failed_attempts = 0
            user.locked_until = None
            user.is_active = True

    print("=" * 60)
    print("✅  Mot de passe réinitialisé avec succès.")
    print(f"    Email    : {email}")
    print(f"    Password : {plain}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(reset())
