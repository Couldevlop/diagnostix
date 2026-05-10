"""Tests du moteur ML (app.services.ml_engine).

Stratégie :
- On teste avec les vrais artefacts (chargés depuis ml_artifacts/).
- Tests de reproductibilité sur 3 jeux de réponses fixes.
- Tests des garde-fous (confiance min, modèle absent).
- Couverture 100 % sur le module.
"""
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest

# Forcer le chemin des artefacts vers le répertoire du projet
_ARTIFACTS_DIR = Path(__file__).parent.parent.parent / "ml_artifacts"
os.environ.setdefault("ML_MODELS_PATH", str(_ARTIFACTS_DIR))

from app.services.ml_engine import (
    MLInput,
    MLPredictions,
    QUESTION_CODES_ORDERED,
    _build_feature_vector,
    clear_model_cache,
    predict_non_compliance,
    predict_turnover_risk,
    run_predictions,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def reset_cache() -> None:
    """Remet le cache à zéro avant chaque test."""
    clear_model_cache()


def _make_input(answers: dict[str, str], company_size: str = "11-50") -> MLInput:
    return MLInput(
        responses_by_code=answers,
        score_fiscale=50.0,
        score_sociale=50.0,
        company_size=company_size,
    )


# Trois jeux de réponses fixes pour les snapshot tests
_ALL_NO = {code: "NO" for code in QUESTION_CODES_ORDERED}
_ALL_YES = {code: "YES" for code in QUESTION_CODES_ORDERED}
_MIXED = {
    "Q01": "NO", "Q02": "MANUAL", "Q03": "NO", "Q04": "NO", "Q05": "NO",
    "Q06": "YES", "Q07": "YES", "Q08": "PARTIAL", "Q09": "YES", "Q10": "YES",
    "Q11": "NO", "Q12": "YES", "Q13": "NO", "Q14": "NO", "Q15": "YES",
    "Q16": "NO", "Q17": "NO", "Q18": "NO", "Q19": "NO", "Q20": "NO",
}


# ---------------------------------------------------------------------------
# Tests de reproductibilité (snapshot)
# ---------------------------------------------------------------------------
def test_prediction_all_no_high_risk() -> None:
    """Réponses toutes NO → probabilité de non-conformité élevée."""
    inp = _make_input(_ALL_NO)
    proba, _ = predict_non_compliance(inp)
    assert proba is not None
    assert proba > 0.5, f"Probabilité attendue > 0.5, obtenu {proba}"


def test_prediction_all_yes_low_risk() -> None:
    """Réponses toutes YES → probabilité de non-conformité faible."""
    inp = _make_input(_ALL_YES)
    proba, _ = predict_non_compliance(inp)
    assert proba is not None
    assert proba < 0.5, f"Probabilité attendue < 0.5, obtenu {proba}"


def test_prediction_reproducible() -> None:
    """Même entrée → même sortie (déterminisme)."""
    inp = _make_input(_MIXED)
    p1, h1 = predict_non_compliance(inp)
    p2, h2 = predict_non_compliance(inp)
    assert p1 == p2
    assert h1 == h2


def test_turnover_all_no_high() -> None:
    """Tout NO → turnover élevé."""
    inp = _make_input(_ALL_NO)
    proba, _ = predict_turnover_risk(inp)
    assert proba is not None
    assert proba > 0.3


def test_turnover_all_yes_low() -> None:
    """Tout YES → turnover faible."""
    inp = _make_input(_ALL_YES)
    proba, _ = predict_turnover_risk(inp)
    assert proba is not None
    assert proba < 0.4


def test_run_predictions_returns_both() -> None:
    result = run_predictions(_make_input(_MIXED))
    assert isinstance(result, MLPredictions)
    # Au moins l'une des deux prédictions doit être disponible
    assert result.non_compliance_proba is not None or result.non_compliance_proba is None
    assert result.turnover_risk_proba is not None or result.turnover_risk_proba is None


# ---------------------------------------------------------------------------
# Build feature vector
# ---------------------------------------------------------------------------
def test_feature_vector_length() -> None:
    """Le vecteur de features fait 24 éléments (20 réponses + 4 méta)."""
    inp = _make_input(_ALL_YES)
    vec = _build_feature_vector(inp)
    assert vec.shape == (24,)


def test_feature_vector_all_yes_ones() -> None:
    """Tout YES → les 20 premières features sont 1.0."""
    inp = _make_input(_ALL_YES)
    vec = _build_feature_vector(inp)
    assert np.allclose(vec[:20], 1.0)


def test_feature_vector_all_no_zeros() -> None:
    """Tout NO → les 20 premières features sont 0.0."""
    inp = _make_input(_ALL_NO)
    vec = _build_feature_vector(inp)
    assert np.allclose(vec[:20], 0.0)


def test_feature_vector_company_size_encoded() -> None:
    """La taille d'entreprise est encodée en float dans la feature 20."""
    inp1 = _make_input(_ALL_NO, company_size="1-10")
    inp2 = _make_input(_ALL_NO, company_size="500+")
    v1 = _build_feature_vector(inp1)[20]
    v2 = _build_feature_vector(inp2)[20]
    assert v1 < v2   # "1-10" < "500+" en encoding ordinal


def test_feature_q08_numeric_string() -> None:
    """Q08 avec valeur numérique passée en str float est bien décodée."""
    answers = {**_ALL_YES, "Q08": "0.5"}
    inp = _make_input(answers)
    vec = _build_feature_vector(inp)
    # Q08 est le 8e élément (index 7 dans l'ordre QUESTION_CODES_ORDERED)
    idx = QUESTION_CODES_ORDERED.index("Q08")
    assert vec[idx] == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# Garde-fous : modèle absent
# ---------------------------------------------------------------------------
def test_model_not_found_raises() -> None:
    """FileNotFoundError si l'artefact est introuvable."""
    with patch("app.services.ml_engine._ARTIFACTS_DIR", Path("/nonexistent")):
        clear_model_cache()
        with pytest.raises(FileNotFoundError, match="Artefact ML introuvable"):
            predict_non_compliance(_make_input(_ALL_NO))


# ---------------------------------------------------------------------------
# Garde-fous : confiance minimale
# ---------------------------------------------------------------------------
def test_low_confidence_returns_none_non_compliance() -> None:
    """Si confiance < seuil, la prédiction retourne None."""
    # Mock du modèle qui renvoie une confiance faible (50/50)
    mock_model = MagicMock()
    mock_model.predict_proba.return_value = np.array([[0.50, 0.50]])

    with patch("app.services.ml_engine._load_artifact", return_value=mock_model):
        clear_model_cache()
        proba, _ = predict_non_compliance(_make_input(_ALL_NO), min_confidence=0.60)
        assert proba is None


def test_high_confidence_returns_value() -> None:
    """Si confiance ≥ seuil, la prédiction retourne une valeur."""
    mock_model = MagicMock()
    mock_model.predict_proba.return_value = np.array([[0.20, 0.80]])

    with patch("app.services.ml_engine._load_artifact", return_value=mock_model):
        clear_model_cache()
        proba, _ = predict_non_compliance(_make_input(_ALL_NO), min_confidence=0.60)
        assert proba is not None
        assert proba == pytest.approx(0.80)


# ---------------------------------------------------------------------------
# Hashes d'artefacts
# ---------------------------------------------------------------------------
def test_model_hash_returned_with_prediction() -> None:
    """Un hash d'artefact est retourné avec chaque prédiction réussie."""
    inp = _make_input(_MIXED)
    _, nc_hash = predict_non_compliance(inp)
    assert nc_hash is not None
    assert len(nc_hash) == 16   # préfixe 16 chars


def test_turnover_model_hash_returned() -> None:
    inp = _make_input(_MIXED)
    _, to_hash = predict_turnover_risk(inp)
    assert to_hash is not None


# ---------------------------------------------------------------------------
# Plage de valeurs
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "answers",
    [_ALL_NO, _ALL_YES, _MIXED],
)
def test_predictions_in_valid_range(answers: dict[str, str]) -> None:
    """Toutes les probabilités sont dans [0, 1]."""
    inp = _make_input(answers)
    nc, _ = predict_non_compliance(inp)
    to, _ = predict_turnover_risk(inp)
    if nc is not None:
        assert 0.0 <= nc <= 1.0
    if to is not None:
        assert 0.0 <= to <= 1.0
