"""Tests du service IA (app.services.ai_service).

Tous les tests utilisent des mocks de l'API Anthropic — aucun appel réseau.
Couvre : parse valide, fallback, cache Redis, retry, validation Pydantic.
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from app.services.ai_service import (
    AIAnalysis,
    Recommendation,
    _build_fallback,
    _build_payload,
    _parse_ai_response,
    get_ai_analysis,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
VALID_JSON = json.dumps({
    "executive_summary": "Votre organisation est en situation de risque élevé.",
    "risk_narrative": "Les risques CNPS et IGR sont critiques.",
    "digital_gap_narrative": "Votre gap digital est de 65 %, très en retard.",
    "recommendations": [
        {
            "priority": 1, "title": "IGR 2024", "description": "Mise à jour paie.",
            "expected_gain_fcfa": 5000000, "implementation_weeks": 4,
            "nexusrh_module": "NexusRH Paie CI",
        },
        {
            "priority": 2, "title": "CNPS", "description": "Automatiser DISA.",
            "expected_gain_fcfa": 3000000, "implementation_weeks": 8,
            "nexusrh_module": "NexusRH Déclarations",
        },
        {
            "priority": 3, "title": "Portail", "description": "Digitaliser bulletins.",
            "expected_gain_fcfa": 1000000, "implementation_weeks": 12,
            "nexusrh_module": "NexusRH Self-Service",
        },
    ],
    "key_takeaway": "Contactez NexusRH maintenant.",
})

BASE_KWARGS: dict = dict(
    global_score=47.5,
    maturity_level="EMERGENT",
    scores_by_category={"FISCALE": 60, "SOCIALE": 40, "CONFORMITE": 50, "DIGITALE": 35},
    risks_detected=[{"code": "R-FISC-01", "severity": "HIGH", "fcfa_impact": 5000000}],
    financial_exposure=18_500_000,
    non_compliance_proba=0.34,
    digital_gap_pct=65.0,
)


def _mock_client(text: str) -> MagicMock:
    mock = MagicMock()
    msg = MagicMock()
    msg.content = [MagicMock(text=text)]
    msg.usage = MagicMock(input_tokens=500, output_tokens=400)
    mock.messages.create.return_value = msg
    return mock


# ---------------------------------------------------------------------------
# _parse_ai_response
# ---------------------------------------------------------------------------
def test_parse_valid_json() -> None:
    result = _parse_ai_response(VALID_JSON)
    assert isinstance(result, AIAnalysis)
    assert result.executive_summary.startswith("Votre")
    assert len(result.recommendations) == 3


def test_parse_json_with_markdown_fence() -> None:
    """Retire les backticks markdown si présents."""
    wrapped = f"```json\n{VALID_JSON}\n```"
    result = _parse_ai_response(wrapped)
    assert isinstance(result, AIAnalysis)


def test_parse_invalid_json_raises() -> None:
    import json as _json
    with pytest.raises(_json.JSONDecodeError):
        _parse_ai_response("{invalid json}")


def test_parse_missing_field_raises() -> None:
    data = json.loads(VALID_JSON)
    del data["executive_summary"]
    with pytest.raises(Exception):  # ValidationError
        _parse_ai_response(json.dumps(data))


def test_parse_wrong_priorities_raises() -> None:
    data = json.loads(VALID_JSON)
    data["recommendations"][0]["priority"] = 4  # invalide
    data["recommendations"][1]["priority"] = 4
    with pytest.raises(Exception):
        _parse_ai_response(json.dumps(data))


# ---------------------------------------------------------------------------
# _build_fallback
# ---------------------------------------------------------------------------
def test_fallback_is_valid_analysis() -> None:
    result = _build_fallback(40.0, "EMERGENT", 5_000_000)
    assert isinstance(result, AIAnalysis)
    assert len(result.recommendations) == 3
    assert sorted(r.priority for r in result.recommendations) == [1, 2, 3]


def test_fallback_mentions_score() -> None:
    result = _build_fallback(75.0, "OPTIMISE", 2_000_000)
    assert "75.0" in result.executive_summary


def test_fallback_all_maturity_levels() -> None:
    for level in ["CRITIQUE", "EMERGENT", "STRUCTURE", "OPTIMISE", "IA_NATIVE", "UNKNOWN"]:
        result = _build_fallback(50.0, level, 0)
        assert isinstance(result, AIAnalysis)


# ---------------------------------------------------------------------------
# _build_payload
# ---------------------------------------------------------------------------
def test_build_payload_contains_score() -> None:
    payload = _build_payload(47.5, "EMERGENT", {}, [], 5000, None, 65.0)
    assert "47.5" in payload
    assert "EMERGENT" in payload
    assert "Donnée insuffisante" in payload


def test_build_payload_with_proba() -> None:
    payload = _build_payload(47.5, "EMERGENT", {}, [], 5000, 0.34, 65.0)
    assert "34.0%" in payload


# ---------------------------------------------------------------------------
# get_ai_analysis — appel réussi du premier coup
# ---------------------------------------------------------------------------
def test_success_on_first_attempt() -> None:
    client = _mock_client(VALID_JSON)
    result = get_ai_analysis(**BASE_KWARGS, anthropic_client=client)
    assert isinstance(result, AIAnalysis)
    client.messages.create.assert_called_once()


# ---------------------------------------------------------------------------
# get_ai_analysis — retry + fallback
# ---------------------------------------------------------------------------
def test_fallback_on_invalid_json() -> None:
    """Deux tentatives avec JSON invalide → fallback statique."""
    client = _mock_client("{broken json}")
    result = get_ai_analysis(**BASE_KWARGS, anthropic_client=client)
    assert isinstance(result, AIAnalysis)
    # Fallback déclenché après 2 échecs
    assert client.messages.create.call_count == 2


def test_retry_succeeds_on_second_attempt() -> None:
    """Premier appel invalide, deuxième valide → succès sur retry."""
    bad_msg = MagicMock()
    bad_msg.content = [MagicMock(text="{broken}")]
    bad_msg.usage = MagicMock(input_tokens=100, output_tokens=50)

    good_msg = MagicMock()
    good_msg.content = [MagicMock(text=VALID_JSON)]
    good_msg.usage = MagicMock(input_tokens=500, output_tokens=400)

    client = MagicMock()
    client.messages.create.side_effect = [bad_msg, good_msg]

    result = get_ai_analysis(**BASE_KWARGS, anthropic_client=client)
    assert isinstance(result, AIAnalysis)
    assert client.messages.create.call_count == 2


def test_fallback_on_api_error() -> None:
    """Erreur API Anthropic → fallback immédiat."""
    import anthropic as _anthropic
    client = MagicMock()
    client.messages.create.side_effect = _anthropic.APIError(
        message="Service unavailable", request=MagicMock(), body={}
    )
    result = get_ai_analysis(**BASE_KWARGS, anthropic_client=client)
    assert isinstance(result, AIAnalysis)


# ---------------------------------------------------------------------------
# get_ai_analysis — cache Redis
# ---------------------------------------------------------------------------
def test_cache_hit_avoids_api_call() -> None:
    """Si le cache Redis contient la réponse, l'API n'est pas appelée."""
    client = _mock_client(VALID_JSON)
    redis = MagicMock()

    # Sérialiser une AIAnalysis valide pour simuler un hit de cache
    cached_analysis = _parse_ai_response(VALID_JSON)
    redis.get.return_value = cached_analysis.model_dump_json().encode()

    result = get_ai_analysis(**BASE_KWARGS, anthropic_client=client, redis_client=redis)
    assert isinstance(result, AIAnalysis)
    client.messages.create.assert_not_called()


def test_cache_miss_writes_to_redis() -> None:
    """Cache miss → appel API → écriture dans Redis."""
    client = _mock_client(VALID_JSON)
    redis = MagicMock()
    redis.get.return_value = None  # cache miss

    get_ai_analysis(**BASE_KWARGS, anthropic_client=client, redis_client=redis)

    client.messages.create.assert_called_once()
    redis.setex.assert_called_once()


def test_redis_read_error_does_not_crash() -> None:
    """Une exception Redis lors de la lecture n'interrompt pas le service."""
    client = _mock_client(VALID_JSON)
    redis = MagicMock()
    redis.get.side_effect = Exception("Redis down")

    result = get_ai_analysis(**BASE_KWARGS, anthropic_client=client, redis_client=redis)
    assert isinstance(result, AIAnalysis)


def test_redis_write_error_does_not_crash() -> None:
    """Une exception Redis lors de l'écriture n'interrompt pas le service."""
    client = _mock_client(VALID_JSON)
    redis = MagicMock()
    redis.get.return_value = None
    redis.setex.side_effect = Exception("Redis down")

    result = get_ai_analysis(**BASE_KWARGS, anthropic_client=client, redis_client=redis)
    assert isinstance(result, AIAnalysis)


# ---------------------------------------------------------------------------
# Modèle Recommendation
# ---------------------------------------------------------------------------
def test_recommendation_model_valid() -> None:
    r = Recommendation(
        priority=1, title="T", description="D",
        expected_gain_fcfa=100, implementation_weeks=2, nexusrh_module="M",
    )
    assert r.priority == 1


def test_recommendation_invalid_priority() -> None:
    with pytest.raises(Exception):
        Recommendation(
            priority=5, title="T", description="D",  # priority > 3
            expected_gain_fcfa=100, implementation_weeks=2, nexusrh_module="M",
        )
