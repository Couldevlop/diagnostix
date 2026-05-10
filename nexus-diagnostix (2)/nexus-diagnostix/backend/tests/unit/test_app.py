"""Tests de l'application FastAPI : healthchecks, CORS, headers de sécurité."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_healthz(client: AsyncClient) -> None:
    """Le endpoint liveness répond 200 OK."""
    response = await client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_readyz(client: AsyncClient) -> None:
    """Le endpoint readiness répond 200 OK."""
    response = await client.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


@pytest.mark.asyncio
async def test_security_headers(client: AsyncClient) -> None:
    """Les en-têtes de sécurité sont systématiquement appliqués."""
    response = await client.get("/healthz")
    assert response.headers["strict-transport-security"].startswith("max-age=")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"


@pytest.mark.asyncio
async def test_openapi_documentation(client: AsyncClient) -> None:
    """La documentation OpenAPI est exposée et bien préfixée."""
    response = await client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    payload = response.json()
    assert payload["info"]["title"] == "Nexus-Diagnostix API"
    assert payload["info"]["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_root_routes_registered(client: AsyncClient) -> None:
    """Toutes les sections de l'API v1 sont enregistrées."""
    response = await client.get("/api/v1/openapi.json")
    paths = response.json()["paths"]
    assert any(p.startswith("/api/v1/sessions") for p in paths)
    assert any(p.startswith("/api/v1/reports") for p in paths)
    assert any(p.startswith("/api/v1/admin") for p in paths)
    assert any(p.startswith("/api/v1/auth") for p in paths)
