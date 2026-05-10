"""Fixtures partagées pour les tests pytest."""
from __future__ import annotations

import os
from collections.abc import AsyncIterator
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# --- Variables d'env minimales pour que les Settings se chargent ---
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
os.environ.setdefault("ML_MODELS_PATH", str(
    __import__("pathlib").Path(__file__).parent.parent / "ml_artifacts"
))


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


# ---------------------------------------------------------------------------
# Fixtures pour les tests d'intégration avec SQLite en mémoire
# ---------------------------------------------------------------------------
@pytest.fixture
async def sqlite_engine() -> Any:
    """Moteur SQLite en mémoire pour les tests d'intégration sans PostgreSQL.

    On patche le compilateur SQLite pour accepter JSONB (→ TEXT) et UUID (→ TEXT).
    """
    try:
        import aiosqlite  # noqa: F401
    except ImportError:
        pytest.skip("aiosqlite non disponible")

    # Patch du compilateur SQLite pour les types PostgreSQL non natifs
    from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler
    from sqlalchemy.dialects.postgresql import JSONB as _JSONB

    def _visit_JSONB(self: Any, type_: Any, **kw: Any) -> str:
        return "TEXT"

    def _visit_pg_uuid(self: Any, type_: Any, **kw: Any) -> str:
        return "TEXT"

    SQLiteTypeCompiler.visit_JSONB = _visit_JSONB          # type: ignore[attr-defined]
    SQLiteTypeCompiler.visit_UUID = _visit_pg_uuid          # type: ignore[attr-defined]

    # Patch du ResultProcessor de UUID pour que SQLite renvoie les UUID en str
    from sqlalchemy.dialects.postgresql import UUID as _PG_UUID
    _orig_result = _PG_UUID.result_processor

    def _uuid_result_processor(self: Any, dialect: Any, coltype: Any) -> Any:
        if dialect.name == "sqlite":
            import uuid as _uuid_mod
            def process(value: Any) -> Any:
                if value is None:
                    return None
                try:
                    return _uuid_mod.UUID(str(value))
                except (ValueError, AttributeError):
                    return value
            return process
        return _orig_result(self, dialect, coltype)

    _PG_UUID.result_processor = _uuid_result_processor  # type: ignore[method-assign]

    from app.database import Base
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(sqlite_engine: Any) -> AsyncIterator[AsyncSession]:
    """Session de base de données pour les tests d'intégration."""
    session_factory = async_sessionmaker(
        bind=sqlite_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session


@pytest.fixture
async def api_client(app: FastAPI, sqlite_engine: Any) -> AsyncIterator[AsyncClient]:
    """Client API avec BDD SQLite injectée via dependency override."""
    from app.database import get_db
    from sqlalchemy.ext.asyncio import AsyncSession as AS

    session_factory = async_sessionmaker(
        bind=sqlite_engine, class_=AS, expire_on_commit=False, autoflush=False
    )

    async def override_get_db() -> AsyncIterator[AS]:
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
