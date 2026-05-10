"""Tests d'intégration pour les endpoints auth et admin.

Utilisent SQLite en mémoire via les fixtures `api_client` / `db_session`.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.security import hash_password
from app.models.user import User


# ---------------------------------------------------------------------------
# Helper : crée un user admin en BDD
# ---------------------------------------------------------------------------
async def _create_admin(db_session: "Any", email: str = "admin@test.ci", password: str = "AdminPass1234!") -> User:  # type: ignore[name-defined]
    from typing import Any
    user = User(
        email=email,
        password_hash=hash_password(password, rounds=4),
        role="ADMIN",
        is_active=True,
        failed_attempts=0,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


# ---------------------------------------------------------------------------
# POST /api/v1/auth/login
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_login_success(api_client: AsyncClient, db_session: "Any") -> None:  # type: ignore[name-defined]
    await _create_admin(db_session)
    resp = await api_client.post("/api/v1/auth/login", json={
        "email": "admin@test.ci", "password": "AdminPass1234!",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(api_client: AsyncClient, db_session: "Any") -> None:  # type: ignore[name-defined]
    await _create_admin(db_session)
    resp = await api_client.post("/api/v1/auth/login", json={
        "email": "admin@test.ci", "password": "WrongPassword!",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email(api_client: AsyncClient, db_session: "Any") -> None:  # type: ignore[name-defined]
    resp = await api_client.post("/api/v1/auth/login", json={
        "email": "nobody@test.ci", "password": "SomePass123!",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_bruteforce_locks_account(api_client: AsyncClient, db_session: "Any") -> None:  # type: ignore[name-defined]
    """5 échecs consécutifs → compte verrouillé (403)."""
    await _create_admin(db_session, email="brute@test.ci")
    for _ in range(5):
        await api_client.post("/api/v1/auth/login", json={
            "email": "brute@test.ci", "password": "WrongPass!",
        })
    resp = await api_client.post("/api/v1/auth/login", json={
        "email": "brute@test.ci", "password": "WrongPass!",
    })
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# POST /api/v1/auth/refresh
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_refresh_token_success(api_client: AsyncClient, db_session: "Any") -> None:  # type: ignore[name-defined]
    await _create_admin(db_session)
    login_resp = await api_client.post("/api/v1/auth/login", json={
        "email": "admin@test.ci", "password": "AdminPass1234!",
    })
    token = login_resp.json()["access_token"]
    resp = await api_client.post("/api/v1/auth/refresh", json={"refresh_token": token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_refresh_invalid_token(api_client: AsyncClient, db_session: "Any") -> None:  # type: ignore[name-defined]
    resp = await api_client.post("/api/v1/auth/refresh", json={"refresh_token": "garbage.token.here"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Admin questions
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_admin_list_questions_requires_auth(api_client: AsyncClient) -> None:
    resp = await api_client.get("/api/v1/admin/questions")
    assert resp.status_code == 422  # Header manquant → pydantic validation error


@pytest.mark.asyncio
async def test_admin_list_questions_invalid_token(api_client: AsyncClient) -> None:
    resp = await api_client.get(
        "/api/v1/admin/questions",
        headers={"Authorization": "Bearer fake.token.here"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_admin_list_questions_success(api_client: AsyncClient, db_session: "Any") -> None:  # type: ignore[name-defined]
    await _create_admin(db_session)
    login_resp = await api_client.post("/api/v1/auth/login", json={
        "email": "admin@test.ci", "password": "AdminPass1234!",
    })
    token = login_resp.json()["access_token"]

    resp = await api_client.get(
        "/api/v1/admin/questions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert "questions" in resp.json()


@pytest.mark.asyncio
async def test_admin_update_question(api_client: AsyncClient, db_session: "Any") -> None:  # type: ignore[name-defined]
    from app.models.question import AnswerType, Question, QuestionCategory
    q = Question(
        code="QT1", label="Question test", category=QuestionCategory.FISCALE.value,
        weight=5, answer_type=AnswerType.YES_NO.value, order=99, is_active=True,
    )
    db_session.add(q)
    await db_session.commit()
    await db_session.refresh(q)

    await _create_admin(db_session)
    login_resp = await api_client.post("/api/v1/auth/login", json={
        "email": "admin@test.ci", "password": "AdminPass1234!",
    })
    token = login_resp.json()["access_token"]

    resp = await api_client.put(
        f"/api/v1/admin/questions/{q.id}",
        json={"label": "Question modifiée"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["updated"] is True


@pytest.mark.asyncio
async def test_admin_toggle_question(api_client: AsyncClient, db_session: "Any") -> None:  # type: ignore[name-defined]
    from app.models.question import AnswerType, Question, QuestionCategory
    q = Question(
        code="QT2", label="Toggle test", category=QuestionCategory.DIGITALE.value,
        weight=5, answer_type=AnswerType.YES_NO.value, order=100, is_active=True,
    )
    db_session.add(q)
    await db_session.commit()
    await db_session.refresh(q)

    await _create_admin(db_session)
    login_resp = await api_client.post("/api/v1/auth/login", json={
        "email": "admin@test.ci", "password": "AdminPass1234!",
    })
    token = login_resp.json()["access_token"]

    resp = await api_client.patch(
        f"/api/v1/admin/questions/{q.id}/toggle",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False


# ---------------------------------------------------------------------------
# Admin stats + leads
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_admin_stats(api_client: AsyncClient, db_session: "Any") -> None:  # type: ignore[name-defined]
    await _create_admin(db_session)
    login_resp = await api_client.post("/api/v1/auth/login", json={
        "email": "admin@test.ci", "password": "AdminPass1234!",
    })
    token = login_resp.json()["access_token"]

    resp = await api_client.get(
        "/api/v1/admin/stats",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "total_sessions" in data
    assert "completion_rate" in data


@pytest.mark.asyncio
async def test_admin_leads_empty(api_client: AsyncClient, db_session: "Any") -> None:  # type: ignore[name-defined]
    await _create_admin(db_session)
    login_resp = await api_client.post("/api/v1/auth/login", json={
        "email": "admin@test.ci", "password": "AdminPass1234!",
    })
    token = login_resp.json()["access_token"]

    resp = await api_client.get(
        "/api/v1/admin/leads",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["leads"] == []


@pytest.mark.asyncio
async def test_admin_audit_logs_empty(api_client: AsyncClient, db_session: "Any") -> None:  # type: ignore[name-defined]
    await _create_admin(db_session)
    login_resp = await api_client.post("/api/v1/auth/login", json={
        "email": "admin@test.ci", "password": "AdminPass1234!",
    })
    token = login_resp.json()["access_token"]

    resp = await api_client.get(
        "/api/v1/admin/audit-logs",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["audit_logs"] == []
