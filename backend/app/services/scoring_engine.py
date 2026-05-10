"""Moteur de scoring déterministe (§8.2 du CLAUDE.md).

Calcule les scores par catégorie, le score global, le niveau de maturité
et le gap digital — uniquement à partir des données passées en paramètre,
sans accès BDD. 100 % reproductible à la décimale près.
"""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Final

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
CATEGORY_WEIGHTS: Final[dict[str, float]] = {
    "FISCALE": 0.20,
    "SOCIALE": 0.20,
    "CONFORMITE": 0.20,
    "DIGITALE": 0.40,
}

# (seuil_minimum_inclus, libellé)
MATURITY_THRESHOLDS: Final[list[tuple[float, str]]] = [
    (85.0, "IA_NATIVE"),
    (70.0, "OPTIMISE"),
    (50.0, "STRUCTURE"),
    (30.0, "EMERGENT"),
    (0.0,  "CRITIQUE"),
]

ANSWER_VALUES: Final[dict[str, float]] = {
    "YES":     1.00,
    "PARTIAL": 0.50,
    "MANUAL":  0.25,
    "NO":      0.00,
}

FREE_NUMERIC_MAX_HOURS: Final[float] = 40.0


# ---------------------------------------------------------------------------
# Structures de données
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class QuestionMeta:
    """Métadonnées d'une question nécessaires au calcul."""

    code: str
    category: str
    weight: int
    answer_type: str  # YES_NO | YES_NO_PARTIAL | YES_NO_MANUAL | FREE_NUMERIC


@dataclass(frozen=True)
class ResponseInput:
    """Réponse brute d'un utilisateur à une question."""

    question_code: str
    answer_value: str
    answer_numeric: float | None = None


@dataclass(frozen=True)
class ScoreResult:
    """Résultat complet du calcul de score."""

    global_score: float
    score_fiscale: float
    score_sociale: float
    score_conformite: float
    score_digitale: float
    maturity_level: str
    digital_gap_pct: float
    scores_by_category: dict[str, float] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Fonctions utilitaires
# ---------------------------------------------------------------------------
def map_answer_to_value(
    answer_type: str,
    answer_value: str,
    answer_numeric: float | None,
) -> float:
    """Convertit une réponse brute en valeur numérique [0, 1]."""
    if answer_type == "FREE_NUMERIC":
        hours = answer_numeric if answer_numeric is not None else 0.0
        return min(1.0, max(0.0, 1.0 - hours / FREE_NUMERIC_MAX_HOURS))
    return ANSWER_VALUES.get(answer_value.upper(), 0.0)


def get_maturity_level(global_score: float) -> str:
    """Retourne le niveau de maturité pour un score global donné."""
    for threshold, level in MATURITY_THRESHOLDS:
        if global_score >= threshold:
            return level
    return "CRITIQUE"


def _compute_category_score(weighted_items: list[tuple[int, float]]) -> float:
    """S_c = (Σ poids_i × valeur_i) / (Σ poids_i) × 100."""
    total_weight = sum(w for w, _ in weighted_items)
    if total_weight == 0:
        return 0.0
    weighted_sum = sum(w * v for w, v in weighted_items)
    return weighted_sum / total_weight * 100.0


def _compute_digital_gap(
    questions: list[QuestionMeta],
    response_map: dict[str, ResponseInput],
) -> float:
    """Distance euclidienne pondérée normalisée vs le vecteur IA-NATIVE (§8.4.3).

    gap = sqrt(Σ wi × (1 − vi)²) / sqrt(Σ wi) × 100
    - gap = 0 % → client = IA-NATIVE
    - gap = 100 % → toutes les réponses = NO / 0
    """
    sum_wi_delta_sq = 0.0
    sum_wi = 0.0
    for q in questions:
        resp = response_map.get(q.code)
        v = 0.0
        if resp is not None:
            v = map_answer_to_value(q.answer_type, resp.answer_value, resp.answer_numeric)
        w = float(q.weight)
        sum_wi_delta_sq += w * (1.0 - v) ** 2
        sum_wi += w
    if sum_wi == 0.0:
        return 100.0
    return math.sqrt(sum_wi_delta_sq / sum_wi) * 100.0


# ---------------------------------------------------------------------------
# Point d'entrée principal
# ---------------------------------------------------------------------------
def compute_scores(
    questions: list[QuestionMeta],
    responses: list[ResponseInput],
) -> ScoreResult:
    """Calcule tous les scores à partir des questions et des réponses.

    Les questions non répondues contribuent avec une valeur 0.
    """
    response_map: dict[str, ResponseInput] = {r.question_code: r for r in responses}

    # Groupe les items (weight, value) par catégorie
    by_cat: dict[str, list[tuple[int, float]]] = defaultdict(list)
    for q in questions:
        resp = response_map.get(q.code)
        v = (
            map_answer_to_value(q.answer_type, resp.answer_value, resp.answer_numeric)
            if resp is not None
            else 0.0
        )
        by_cat[q.category].append((q.weight, v))

    # Scores par catégorie
    cat_scores: dict[str, float] = {
        cat: _compute_category_score(by_cat.get(cat, []))
        for cat in CATEGORY_WEIGHTS
    }

    global_score = sum(
        CATEGORY_WEIGHTS[cat] * cat_scores[cat] for cat in CATEGORY_WEIGHTS
    )
    global_score = round(global_score, 2)

    digital_gap = _compute_digital_gap(questions, response_map)

    return ScoreResult(
        global_score=global_score,
        score_fiscale=round(cat_scores["FISCALE"], 2),
        score_sociale=round(cat_scores["SOCIALE"], 2),
        score_conformite=round(cat_scores["CONFORMITE"], 2),
        score_digitale=round(cat_scores["DIGITALE"], 2),
        maturity_level=get_maturity_level(global_score),
        digital_gap_pct=round(digital_gap, 2),
        scores_by_category=cat_scores,
    )
