"""Fixtures partagées pour les tests pytest."""
from __future__ import annotations

import os
from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

# --- Variables d'env minimales pour que les Settings se chargent ---
# (utilisées par les tests unitaires qui n'ont pas besoin d'une vraie BDD)
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-unit-tests-only-32-chars")
os.environ.setdefault("FIELD_ENCRYPTION_KEY", "Vw0w8K9p1J2qR3sT4uV5wX6yZ7AbCdEfGhIjKl9mNoQ=")
os.environ.setdefault("PDF_SIGNING_SECRET", "test-pdf-signing-secret-32-characters-min")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://nexus:nexus_dev_password@localhost:5432/nexus_test",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test-key-not-real")
os.environ.setdefault("ENVIRONMENT", "development")


@pytest.fixture
def app() -> FastAPI:
    """Instance FastAPI fraîche pour chaque test."""
    from app.main import create_app
    return create_app()


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Client HTTP asynchrone (sans réseau) — utilise ASGITransport."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
