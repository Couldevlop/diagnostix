"""Point d'entrée de l'application FastAPI.

Ce module assemble les routeurs, les middlewares de sécurité, le cycle de vie
applicatif (connexions BDD, Redis, modèles ML) et l'observabilité.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.config import get_settings
from app.core.exceptions import AppException

settings = get_settings()

# --- Configuration des logs structurés -------------------------------------
logging.basicConfig(
    format="%(message)s",
    level=settings.log_level,
)
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
)
logger = structlog.get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Cycle de vie applicatif (startup / shutdown)."""
    logger.info("app.startup", environment=settings.environment, version=app.version)
    # Hooks d'initialisation : connexions, modèles ML, etc. seront ajoutés ici
    # par les sprints suivants. À ce stade, l'app démarre proprement à vide.
    yield
    logger.info("app.shutdown")


def create_app() -> FastAPI:
    """Factory FastAPI (facilite les tests et la réutilisation)."""
    app = FastAPI(
        title="Nexus-Diagnostix API",
        description=(
            "API de l'outil d'auto-diagnostic de maturité digitale RH "
            "pour les entreprises ivoiriennes."
        ),
        version="1.0.0",
        docs_url="/api/v1/docs",
        redoc_url="/api/v1/redoc",
        openapi_url="/api/v1/openapi.json",
        lifespan=lifespan,
    )

    # --- CORS ---------------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    # --- Headers de sécurité ------------------------------------------------
    @app.middleware("http")
    async def security_headers_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        if settings.is_production:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "frame-ancestors 'none'"
            )
        return response

    # --- Gestion centralisée des exceptions métier --------------------------
    @app.exception_handler(AppException)
    async def app_exception_handler(_: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "type": exc.code,
                "title": exc.title,
                "status": exc.status_code,
                "detail": exc.detail,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        """Capture toutes les exceptions non gérées pour garantir les headers CORS."""
        logger.error("unhandled_exception", exc_type=type(exc).__name__, exc=str(exc))
        return JSONResponse(
            status_code=500,
            content={
                "type": "INTERNAL_ERROR",
                "title": "Erreur interne du serveur",
                "status": 500,
                "detail": "Une erreur inattendue s'est produite.",
            },
        )

    # --- Routes ---
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/healthz", tags=["system"], status_code=status.HTTP_200_OK)
    async def healthz() -> dict[str, str]:
        """Liveness probe — l'app est démarrée."""
        return {"status": "ok"}

    @app.get("/readyz", tags=["system"], status_code=status.HTTP_200_OK)
    async def readyz() -> dict[str, str]:
        """Readiness probe — l'app est prête à servir.

        Une version complète vérifiera ici la BDD, Redis, et la disponibilité
        de l'API Anthropic. À ce stade nous renvoyons OK pour permettre le
        démarrage Docker initial.
        """
        return {"status": "ready"}

    return app


app = create_app()
