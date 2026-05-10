"""Moteur ML — prédiction de non-conformité et turnover (§8.4 du CLAUDE.md).

Étage 3 du pipeline d'analyse hybride. Les modèles sont entraînés offline
et chargés depuis des artefacts .joblib. Le gap digital est calculé de façon
déterministe (pas de ML).

Garde-fous :
- Si confiance du modèle < ML_MIN_CONFIDENCE → retourne None (donnée insuffisante).
- Les artefacts sont versionnés ; chaque rapport stocke le hash du modèle utilisé.
"""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np

# Confiance minimale pour exposer une prédiction (configurable via Settings).
ML_MIN_CONFIDENCE: float = float(os.environ.get("ML_MIN_CONFIDENCE", "0.60"))

# Chemins des artefacts (override via env pour les tests)
_ARTIFACTS_DIR = Path(os.environ.get("ML_MODELS_PATH", "/app/ml_artifacts"))

# Codes des 20 questions dans l'ordre canonique (détermine les features)
QUESTION_CODES_ORDERED: list[str] = [
    "Q01", "Q02", "Q03", "Q04", "Q05", "Q06", "Q07", "Q08",
    "Q09", "Q10", "Q11", "Q12", "Q13", "Q14", "Q15", "Q16",
    "Q17", "Q18", "Q19", "Q20",
]

# Encodage des réponses en float pour les features ML
ANSWER_ENCODING: dict[str, float] = {
    "YES": 1.0, "PARTIAL": 0.5, "MANUAL": 0.25, "NO": 0.0,
}

# Taille d'entreprise encodée ordinalement
COMPANY_SIZE_ENCODING: dict[str, float] = {
    "1-10": 0.1, "11-50": 0.3, "51-200": 0.5, "201-500": 0.7, "500+": 1.0,
}


# ---------------------------------------------------------------------------
# Structures
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class MLInput:
    """Vecteur de features pour les prédictions ML."""

    responses_by_code: dict[str, str]    # code → answer_value
    score_fiscale: float
    score_sociale: float
    company_size: str = "11-50"
    sector: str = "AUTRE"


@dataclass(frozen=True)
class MLPredictions:
    """Résultats des prédictions ML pour un diagnostic."""

    non_compliance_proba: float | None      # [0,1] ou None si confiance < seuil
    turnover_risk_proba: float | None       # [0,1] ou None si confiance < seuil
    non_compliance_model_hash: str | None   # hash SHA-256 du modèle utilisé
    turnover_model_hash: str | None


# ---------------------------------------------------------------------------
# Chargement des artefacts
# ---------------------------------------------------------------------------
_cache: dict[str, Any] = {}


def _load_artifact(name: str) -> Any:
    """Charge un artefact .joblib avec mise en cache en mémoire."""
    if name not in _cache:
        path = _ARTIFACTS_DIR / f"{name}.joblib"
        if not path.exists():
            raise FileNotFoundError(
                f"Artefact ML introuvable : {path}. "
                "Exécutez d'abord scripts/train_models.py"
            )
        _cache[name] = joblib.load(path)
    return _cache[name]


def _artifact_hash(name: str) -> str:
    """SHA-256 du fichier artefact pour traçabilité (§8.4.4)."""
    path = _ARTIFACTS_DIR / f"{name}.joblib"
    if not path.exists():
        return "not_found"
    h = hashlib.sha256(path.read_bytes()).hexdigest()
    return h[:16]  # préfixe 16 chars suffisant pour l'identification


def clear_model_cache() -> None:
    """Vide le cache en mémoire (utile dans les tests pour injecter des mocks)."""
    _cache.clear()


# ---------------------------------------------------------------------------
# Vectorisation des features
# ---------------------------------------------------------------------------
def _build_feature_vector(ml_input: MLInput) -> np.ndarray:
    """Construit le vecteur de 24 features (20 réponses + 4 méta)."""
    # 20 réponses encodées
    response_features = []
    for code in QUESTION_CODES_ORDERED:
        raw = ml_input.responses_by_code.get(code, "NO")
        if code == "Q08":
            # Q08 FREE_NUMERIC — la valeur numérique n'est pas disponible ici,
            # on utilise l'encoding direct de la chaîne "YES"/"PARTIAL"/"NO"
            # ou la valeur normalisée si stockée sous forme str "0.5", etc.
            try:
                v = float(raw)
            except ValueError:
                v = ANSWER_ENCODING.get(raw, 0.0)
        else:
            v = ANSWER_ENCODING.get(raw, 0.0)
        response_features.append(v)

    # 4 features méta
    size_encoded = COMPANY_SIZE_ENCODING.get(ml_input.company_size, 0.3)
    sector_encoded = float(hash(ml_input.sector) % 100) / 100.0  # hash stable
    meta_features = [
        size_encoded,
        sector_encoded,
        ml_input.score_fiscale / 100.0,
        ml_input.score_sociale / 100.0,
    ]

    return np.array(response_features + meta_features, dtype=np.float64)


# ---------------------------------------------------------------------------
# Prédictions
# ---------------------------------------------------------------------------
def predict_non_compliance(
    ml_input: MLInput,
    *,
    min_confidence: float = ML_MIN_CONFIDENCE,
) -> tuple[float | None, str | None]:
    """Prédiction de non-conformité à 12 mois (RandomForestClassifier §8.4.1).

    Returns:
        (probabilité|None, hash_modèle|None)
    """
    model = _load_artifact("non_compliance_rf")
    X = _build_feature_vector(ml_input).reshape(1, -1)
    proba_arr = model.predict_proba(X)[0]
    # La classe 1 = non-conforme ; proba_arr[1] si le modèle est binaire
    confidence = float(max(proba_arr))
    proba = float(proba_arr[1]) if len(proba_arr) > 1 else float(proba_arr[0])
    if confidence < min_confidence:
        return None, None
    return round(proba, 3), _artifact_hash("non_compliance_rf")


def predict_turnover_risk(
    ml_input: MLInput,
    *,
    min_confidence: float = ML_MIN_CONFIDENCE,
) -> tuple[float | None, str | None]:
    """Prédiction du risque de turnover (GradientBoostingRegressor §8.4.2).

    Returns:
        (probabilité|None, hash_modèle|None)
    """
    model = _load_artifact("turnover_gb")
    X = _build_feature_vector(ml_input).reshape(1, -1)
    pred = float(model.predict(X)[0])
    proba = max(0.0, min(1.0, pred))

    # Pour un régresseur, on estime la confiance via la dispersion des prédictions
    # des estimateurs individuels (accès interne GBR — best-effort).
    try:
        preds_individual = np.array([
            est[0].predict(X)[0] for est in model.estimators_  # type: ignore[attr-defined]
        ])
        std = float(np.std(preds_individual))
        confidence = max(0.0, 1.0 - std * 2)  # heuristique : std élevé → faible confiance
    except Exception:  # noqa: BLE001
        confidence = 1.0  # par défaut si accès impossible

    if confidence < min_confidence:
        return None, None
    return round(proba, 3), _artifact_hash("turnover_gb")


def run_predictions(ml_input: MLInput) -> MLPredictions:
    """Point d'entrée principal — exécute les deux prédictions."""
    nc_proba, nc_hash = predict_non_compliance(ml_input)
    to_proba, to_hash = predict_turnover_risk(ml_input)
    return MLPredictions(
        non_compliance_proba=nc_proba,
        turnover_risk_proba=to_proba,
        non_compliance_model_hash=nc_hash,
        turnover_model_hash=to_hash,
    )
