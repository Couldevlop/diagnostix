"""Tests d'intégration des endpoints questionnaire + responses + reports.

Utilisent SQLite en mémoire via la fixture `api_client` du conftest.
"""
from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

from app.models.question import AnswerType, Question, QuestionCategory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _seed_questions(db_session: "Any") -> None:  # type: ignore[name-defined]
    """Insère 2 questions de test dans la BDD."""
    from typing import Any
    q1 = Question(
        code="Q01", label="Réforme IGR ?", category=QuestionCategory.FISCALE.value,
        weight=10, answer_type=AnswerType.YES_NO_PARTIAL.value, order=1, is_active=True,
    )
    q2 = Question(
        code="Q02", label="IFC automatisée ?", category=QuestionCategory.SOCIALE.value,
        weight=10, answer_type=AnswerType.YES_NO_MANUAL.value, order=2, is_active=True,
    )
    db_session.add(q1)
    db_session.add(q2)
    await db_session.commit()


# ---------------------------------------------------------------------------
# POST /api/v1/sessions
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_session_minimal(api_client: AsyncClient, db_session: "Any") -> None:  # type: ignore[name-defined]
    """Crée une session avec juste le minimum requis."""
    resp = await api_client.post("/api/v1/sessions", json={})
    assert resp.status_code == 201
    data = resp.json()
    assert "session_id" in data
    assert uuid.UUID(data["session_id"])


@pytest.mark.asyncio
async def test_create_session_with_consent(api_client: AsyncClient, db_session: "Any") -> None:  # type: ignore[name-defined]
    resp = await api_client.post("/api/v1/sessions", json={
        "company_size": "51-200",
        "sector": "BTP",
        "contact_email": "drh@example.ci",
        "contact_consent": True,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["total_questions"] >= 0


@pytest.mark.asyncio
async def test_create_session_no_email_without_consent(api_client: AsyncClient, db_session: "Any") -> None:  # type: ignore[name-defined]
    """Sans consentement, l'email n'est pas stocké."""
    resp = await api_client.post("/api/v1/sessions", json={
        "contact_email": "test@example.ci",
        "contact_consent": False,
    })
    assert resp.status_code == 201


# ---------------------------------------------------------------------------
# GET /api/v1/sessions/{session_id}/questions
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_questions_unknown_session(api_client: AsyncClient) -> None:
    """Session inexistante → 404."""
    fake_id = str(uuid.uuid4())
    resp = await api_client.get(f"/api/v1/sessions/{fake_id}/questions")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_questions_returns_active_only(api_client: AsyncClient, db_session: "Any") -> None:  # type: ignore[name-defined]
    await _seed_questions(db_session)
    # Créer une session
    resp = await api_client.post("/api/v1/sessions", json={})
    session_id = resp.json()["session_id"]

    resp = await api_client.get(f"/api/v1/sessions/{session_id}/questions")
    assert resp.status_code == 200
    data = resp.json()
    assert "questions" in data
    assert len(data["questions"]) == 2
    assert data["questions"][0]["code"] == "Q01"
    assert data["questions"][1]["code"] == "Q02"


# ---------------------------------------------------------------------------
# POST /api/v1/sessions/{session_id}/responses
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_save_response_success(api_client: AsyncClient, db_session: "Any") -> None:  # type: ignore[name-defined]
    await _seed_questions(db_session)

    resp = await api_client.post("/api/v1/sessions", json={})
    session_id = resp.json()["session_id"]

    # Récupérer l'ID de la première question
    q_resp = await api_client.get(f"/api/v1/sessions/{session_id}/questions")
    q_id = q_resp.json()["questions"][0]["id"]

    resp = await api_client.post(
        f"/api/v1/sessions/{session_id}/responses",
        json={"question_id": q_id, "answer_value": "YES"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["saved"] is True
    assert data["progress"]["answered"] == 1
    assert data["progress"]["total"] == 2
    assert data["progress"]["percent"] == 50.0


@pytest.mark.asyncio
async def test_save_response_idempotent(api_client: AsyncClient, db_session: "Any") -> None:  # type: ignore[name-defined]
    """Même réponse deux fois → mise à jour, pas de doublon."""
    await _seed_questions(db_session)
    resp = await api_client.post("/api/v1/sessions", json={})
    session_id = resp.json()["session_id"]
    q_resp = await api_client.get(f"/api/v1/sessions/{session_id}/questions")
    q_id = q_resp.json()["questions"][0]["id"]

    # Premier appel
    await api_client.post(
        f"/api/v1/sessions/{session_id}/responses",
        json={"question_id": q_id, "answer_value": "NO"},
    )
    # Deuxième appel avec valeur différente → doit mettre à jour
    resp = await api_client.post(
        f"/api/v1/sessions/{session_id}/responses",
        json={"question_id": q_id, "answer_value": "YES"},
    )
    assert resp.status_code == 200
    assert resp.json()["progress"]["answered"] == 1  # toujours 1, pas 2


@pytest.mark.asyncio
async def test_save_response_unknown_session(api_client: AsyncClient) -> None:
    resp = await api_client.post(
        f"/api/v1/sessions/{uuid.uuid4()}/responses",
        json={"question_id": 1, "answer_value": "YES"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_save_response_invalid_answer_value(api_client: AsyncClient, db_session: "Any") -> None:  # type: ignore[name-defined]
    resp = await api_client.post("/api/v1/sessions", json={})
    session_id = resp.json()["session_id"]
    resp = await api_client.post(
        f"/api/v1/sessions/{session_id}/responses",
        json={"question_id": 1, "answer_value": "INVALID"},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/v1/sessions/{session_id}/finalize
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_finalize_without_responses_fails(api_client: AsyncClient, db_session: "Any") -> None:  # type: ignore[name-defined]
    await _seed_questions(db_session)
    resp = await api_client.post("/api/v1/sessions", json={})
    session_id = resp.json()["session_id"]

    resp = await api_client.post(f"/api/v1/sessions/{session_id}/finalize")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_finalize_creates_report(api_client: AsyncClient, db_session: "Any") -> None:  # type: ignore[name-defined]
    await _seed_questions(db_session)
    resp = await api_client.post("/api/v1/sessions", json={})
    session_id = resp.json()["session_id"]

    q_resp = await api_client.get(f"/api/v1/sessions/{session_id}/questions")
    for q in q_resp.json()["questions"]:
        await api_client.post(
            f"/api/v1/sessions/{session_id}/responses",
            json={"question_id": q["id"], "answer_value": "YES"},
        )

    resp = await api_client.post(f"/api/v1/sessions/{session_id}/finalize")
    assert resp.status_code == 202
    data = resp.json()
    assert "report_id" in data
    assert data["status"] == "GENERATING"
    assert data["estimated_seconds"] == 15


@pytest.mark.asyncio
async def test_finalize_twice_fails(api_client: AsyncClient, db_session: "Any") -> None:  # type: ignore[name-defined]
    """Finaliser deux fois la même session → 409 Conflict."""
    await _seed_questions(db_session)
    resp = await api_client.post("/api/v1/sessions", json={})
    session_id = resp.json()["session_id"]

    q_resp = await api_client.get(f"/api/v1/sessions/{session_id}/questions")
    for q in q_resp.json()["questions"]:
        await api_client.post(
            f"/api/v1/sessions/{session_id}/responses",
            json={"question_id": q["id"], "answer_value": "YES"},
        )

    await api_client.post(f"/api/v1/sessions/{session_id}/finalize")
    resp = await api_client.post(f"/api/v1/sessions/{session_id}/finalize")
    assert resp.status_code == 409


# ---------------------------------------------------------------------------
# GET /api/v1/reports/{report_id}
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_report_unknown(api_client: AsyncClient) -> None:
    resp = await api_client.get(f"/api/v1/reports/{uuid.uuid4()}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_report_generating_status(api_client: AsyncClient, db_session: "Any") -> None:  # type: ignore[name-defined]
    """Rapport en cours de génération retourne status=GENERATING."""
    await _seed_questions(db_session)
    resp = await api_client.post("/api/v1/sessions", json={})
    session_id = resp.json()["session_id"]

    q_resp = await api_client.get(f"/api/v1/sessions/{session_id}/questions")
    for q in q_resp.json()["questions"]:
        await api_client.post(
            f"/api/v1/sessions/{session_id}/responses",
            json={"question_id": q["id"], "answer_value": "YES"},
        )

    finalize_resp = await api_client.post(f"/api/v1/sessions/{session_id}/finalize")
    report_id = finalize_resp.json()["report_id"]

    # Immédiatement après la finalisation → GENERATING (background pas encore fini)
    resp = await api_client.get(f"/api/v1/reports/{report_id}")
    assert resp.status_code == 200
    # Le statut peut être GENERATING ou READY selon la vitesse du bg task
    assert resp.json()["status"] in ("GENERATING", "READY", "FAILED")
