"""Tests du moteur de scoring (app.services.scoring_engine).

Couverture : 100 % — snapshot tests sur 5 cas de référence (CRITIQUE → IA_NATIVE),
tests paramétrés sur map_answer_to_value et get_maturity_level.
"""
from __future__ import annotations

import math

import pytest

from app.services.scoring_engine import (
    QuestionMeta,
    ResponseInput,
    ScoreResult,
    _compute_digital_gap,
    compute_scores,
    get_maturity_level,
    map_answer_to_value,
)

# ---------------------------------------------------------------------------
# Fixtures : les 20 questions du diagnostic
# ---------------------------------------------------------------------------
QUESTIONS: list[QuestionMeta] = [
    QuestionMeta("Q01", "FISCALE",    10, "YES_NO_PARTIAL"),
    QuestionMeta("Q02", "SOCIALE",    10, "YES_NO_MANUAL"),
    QuestionMeta("Q03", "SOCIALE",     5, "YES_NO"),
    QuestionMeta("Q04", "CONFORMITE", 10, "YES_NO"),
    QuestionMeta("Q05", "DIGITALE",    5, "YES_NO_PARTIAL"),
    QuestionMeta("Q06", "DIGITALE",    5, "YES_NO"),
    QuestionMeta("Q07", "DIGITALE",    5, "YES_NO"),
    QuestionMeta("Q08", "DIGITALE",   10, "FREE_NUMERIC"),
    QuestionMeta("Q09", "DIGITALE",    5, "YES_NO"),
    QuestionMeta("Q10", "SOCIALE",     5, "YES_NO"),
    QuestionMeta("Q11", "DIGITALE",   10, "YES_NO"),
    QuestionMeta("Q12", "DIGITALE",    5, "YES_NO"),
    QuestionMeta("Q13", "DIGITALE",    5, "YES_NO"),
    QuestionMeta("Q14", "DIGITALE",    5, "YES_NO"),
    QuestionMeta("Q15", "DIGITALE",    5, "YES_NO"),
    QuestionMeta("Q16", "DIGITALE",   10, "YES_NO"),
    QuestionMeta("Q17", "DIGITALE",    5, "YES_NO"),
    QuestionMeta("Q18", "DIGITALE",   10, "YES_NO"),
    QuestionMeta("Q19", "DIGITALE",    5, "YES_NO"),
    QuestionMeta("Q20", "CONFORMITE", 10, "YES_NO"),
]


def _yes_all() -> list[ResponseInput]:
    """Toutes les questions répondues YES / 0h pour Q08."""
    resp = []
    for q in QUESTIONS:
        if q.answer_type == "FREE_NUMERIC":
            resp.append(ResponseInput(q.code, "FREE_NUMERIC", 0.0))
        else:
            resp.append(ResponseInput(q.code, "YES"))
    return resp


def _no_all() -> list[ResponseInput]:
    """Toutes les questions répondues NO / 40h pour Q08."""
    resp = []
    for q in QUESTIONS:
        if q.answer_type == "FREE_NUMERIC":
            resp.append(ResponseInput(q.code, "FREE_NUMERIC", 40.0))
        else:
            resp.append(ResponseInput(q.code, "NO"))
    return resp


# ---------------------------------------------------------------------------
# map_answer_to_value — conversions
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("answer_type", "answer_value", "answer_numeric", "expected"),
    [
        ("YES_NO",          "YES",     None,  1.00),
        ("YES_NO",          "NO",      None,  0.00),
        ("YES_NO_PARTIAL",  "PARTIAL", None,  0.50),
        ("YES_NO_PARTIAL",  "YES",     None,  1.00),
        ("YES_NO_PARTIAL",  "NO",      None,  0.00),
        ("YES_NO_MANUAL",   "MANUAL",  None,  0.25),
        ("FREE_NUMERIC",    "FREE_NUMERIC", 0.0,   1.00),
        ("FREE_NUMERIC",    "FREE_NUMERIC", 20.0,  0.50),
        ("FREE_NUMERIC",    "FREE_NUMERIC", 40.0,  0.00),
        ("FREE_NUMERIC",    "FREE_NUMERIC", 80.0,  0.00),  # au-delà du max → 0
        ("FREE_NUMERIC",    "FREE_NUMERIC", None,  1.00),  # None → 0h → 1.0
    ],
)
def test_map_answer_to_value(
    answer_type: str,
    answer_value: str,
    answer_numeric: float | None,
    expected: float,
) -> None:
    result = map_answer_to_value(answer_type, answer_value, answer_numeric)
    assert result == pytest.approx(expected), f"{answer_type}/{answer_value} → {result}"


# ---------------------------------------------------------------------------
# get_maturity_level — toutes les frontières
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("score", "level"),
    [
        (0.0,   "CRITIQUE"),
        (15.0,  "CRITIQUE"),
        (29.99, "CRITIQUE"),
        (30.0,  "EMERGENT"),
        (40.0,  "EMERGENT"),
        (49.99, "EMERGENT"),
        (50.0,  "STRUCTURE"),
        (60.0,  "STRUCTURE"),
        (69.99, "STRUCTURE"),
        (70.0,  "OPTIMISE"),
        (77.5,  "OPTIMISE"),
        (84.99, "OPTIMISE"),
        (85.0,  "IA_NATIVE"),
        (100.0, "IA_NATIVE"),
    ],
)
def test_get_maturity_level(score: float, level: str) -> None:
    assert get_maturity_level(score) == level


# ---------------------------------------------------------------------------
# Snapshot tests — 5 jeux de référence (CRITIQUE → IA_NATIVE)
# ---------------------------------------------------------------------------
def test_snapshot_critique() -> None:
    """Toutes les réponses = NO / 40h → score global = 0 → CRITIQUE, gap = 100 %."""
    result = compute_scores(QUESTIONS, _no_all())
    assert result.global_score == 0.0
    assert result.score_fiscale == 0.0
    assert result.score_sociale == 0.0
    assert result.score_conformite == 0.0
    assert result.score_digitale == 0.0
    assert result.maturity_level == "CRITIQUE"
    assert result.digital_gap_pct == pytest.approx(100.0)


def test_snapshot_ia_native() -> None:
    """Toutes YES / 0h → score = 100 → IA_NATIVE, gap = 0 %."""
    result = compute_scores(QUESTIONS, _yes_all())
    assert result.global_score == 100.0
    assert result.score_fiscale == 100.0
    assert result.score_sociale == 100.0
    assert result.score_conformite == 100.0
    assert result.score_digitale == 100.0
    assert result.maturity_level == "IA_NATIVE"
    assert result.digital_gap_pct == pytest.approx(0.0)


def test_snapshot_emergent() -> None:
    """Réponses calibrées pour obtenir un score global ≈ 40 → ÉMERGENT.

    Calcul manuel :
    - FISCALE  : Q01=NO(10)       → 0/10 * 100 = 0
    - SOCIALE  : Q02=YES(10), Q03=YES(5), Q10=YES(5) → 100
    - CONFORMITE: Q04=NO(10), Q20=YES(10) → 50
    - DIGITALE : Q05=PARTIAL(5,0.5), Q06=YES(5), Q07=YES(5), Q08=20h(10,0.5),
                 Q09=YES(5), Q11-Q19=NO → (2.5+5+5+5+5)/90*100 = 22.5/90*100 ≈ 25.0
    Global = 0.2*0 + 0.2*100 + 0.2*50 + 0.4*25 = 0+20+10+10 = 40
    """
    responses = [
        ResponseInput("Q01", "NO"),
        ResponseInput("Q02", "YES"),
        ResponseInput("Q03", "YES"),
        ResponseInput("Q04", "NO"),
        ResponseInput("Q05", "PARTIAL"),
        ResponseInput("Q06", "YES"),
        ResponseInput("Q07", "YES"),
        ResponseInput("Q08", "FREE_NUMERIC", 20.0),
        ResponseInput("Q09", "YES"),
        ResponseInput("Q10", "YES"),
        ResponseInput("Q11", "NO"),
        ResponseInput("Q12", "NO"),
        ResponseInput("Q13", "NO"),
        ResponseInput("Q14", "NO"),
        ResponseInput("Q15", "NO"),
        ResponseInput("Q16", "NO"),
        ResponseInput("Q17", "NO"),
        ResponseInput("Q18", "NO"),
        ResponseInput("Q19", "NO"),
        ResponseInput("Q20", "YES"),
    ]
    result = compute_scores(QUESTIONS, responses)
    assert result.global_score == pytest.approx(40.0, abs=0.01)
    assert result.maturity_level == "EMERGENT"


def test_snapshot_structure() -> None:
    """Réponses calibrées pour un score global ≈ 66.67 → STRUCTURÉ.

    Calcul :
    - FISCALE  : Q01=PARTIAL(10,0.5) → 50
    - SOCIALE  : Q02=YES(10), Q03=YES(5), Q10=YES(5) → 100
    - CONFORMITE: Q04=YES(10), Q20=YES(10) → 100
    - DIGITALE : Q05=PARTIAL(5,0.5)=2.5, Q06/07=YES(5)=5, Q08=20h(10,0.5)=5,
                 Q12=YES(5)=5, Q15=YES(5)=5, Q17=YES(5)=5, Q19=YES(5)=5
                 reste=NO → sum=37.5/90*100=41.67
    Global = 0.2*50 + 0.2*100 + 0.2*100 + 0.4*41.67 = 10+20+20+16.67 = 66.67
    """
    responses = [
        ResponseInput("Q01", "PARTIAL"),
        ResponseInput("Q02", "YES"),
        ResponseInput("Q03", "YES"),
        ResponseInput("Q04", "YES"),
        ResponseInput("Q05", "PARTIAL"),
        ResponseInput("Q06", "YES"),
        ResponseInput("Q07", "YES"),
        ResponseInput("Q08", "FREE_NUMERIC", 20.0),
        ResponseInput("Q09", "NO"),
        ResponseInput("Q10", "YES"),
        ResponseInput("Q11", "NO"),
        ResponseInput("Q12", "YES"),
        ResponseInput("Q13", "NO"),
        ResponseInput("Q14", "NO"),
        ResponseInput("Q15", "YES"),
        ResponseInput("Q16", "NO"),
        ResponseInput("Q17", "YES"),
        ResponseInput("Q18", "NO"),
        ResponseInput("Q19", "YES"),
        ResponseInput("Q20", "YES"),
    ]
    result = compute_scores(QUESTIONS, responses)
    assert result.global_score == pytest.approx(66.67, abs=0.01)
    assert result.maturity_level == "STRUCTURE"


def test_snapshot_optimise() -> None:
    """Réponses calibrées pour un score global = 75 → OPTIMISÉ.

    Calcul :
    - FISCALE  : Q01=YES(10) → 100
    - SOCIALE  : Q02=YES(10), Q03=NO(5), Q10=YES(5) → 15/20*100 = 75
    - CONFORMITE: Q04=YES(10), Q20=YES(10) → 100
    - DIGITALE : Q05-Q09=YES(25 pts, sauf Q08=0h=10), Q11=YES(10), Q12=YES(5),
                 Q13-Q19=NO → (5+5+5+10+5+10+5)/90*100 = 45/90*100 = 50
    Global = 0.2*100 + 0.2*75 + 0.2*100 + 0.4*50 = 20+15+20+20 = 75
    """
    responses = [
        ResponseInput("Q01", "YES"),
        ResponseInput("Q02", "YES"),
        ResponseInput("Q03", "NO"),
        ResponseInput("Q04", "YES"),
        ResponseInput("Q05", "YES"),
        ResponseInput("Q06", "YES"),
        ResponseInput("Q07", "YES"),
        ResponseInput("Q08", "FREE_NUMERIC", 0.0),
        ResponseInput("Q09", "YES"),
        ResponseInput("Q10", "YES"),
        ResponseInput("Q11", "YES"),
        ResponseInput("Q12", "YES"),
        ResponseInput("Q13", "NO"),
        ResponseInput("Q14", "NO"),
        ResponseInput("Q15", "NO"),
        ResponseInput("Q16", "NO"),
        ResponseInput("Q17", "NO"),
        ResponseInput("Q18", "NO"),
        ResponseInput("Q19", "NO"),
        ResponseInput("Q20", "YES"),
    ]
    result = compute_scores(QUESTIONS, responses)
    assert result.global_score == pytest.approx(75.0, abs=0.01)
    assert result.maturity_level == "OPTIMISE"


# ---------------------------------------------------------------------------
# Tests de robustesse
# ---------------------------------------------------------------------------
def test_empty_responses_gives_zero() -> None:
    """Sans réponse, tout est à 0 (questions non répondues = 0)."""
    result = compute_scores(QUESTIONS, [])
    assert result.global_score == 0.0
    assert result.maturity_level == "CRITIQUE"


def test_partial_responses_only_scored_questions() -> None:
    """Seules les questions répondues sont prises en compte pour la catégorie."""
    responses = [ResponseInput("Q01", "YES")]
    result = compute_scores(QUESTIONS, responses)
    # FISCALE : Q01 YES poids 10 → 100, mais les autres questions non répondues = 0
    # Score FISCALE = (10*1.0 + 0 + 0 ...) / total_poids_FISCALE * 100
    # Il n'y a qu'une seule question FISCALE (Q01, weight=10) → 100
    assert result.score_fiscale == pytest.approx(100.0)


def test_score_result_is_frozen_dataclass() -> None:
    """ScoreResult est immutable."""
    result = compute_scores(QUESTIONS, _yes_all())
    with pytest.raises((AttributeError, TypeError)):
        result.global_score = 50.0  # type: ignore[misc]


def test_digital_gap_midpoint() -> None:
    """Q08 = 20h → value = 0.5. Toutes autres = YES → gap intermédiaire."""
    responses = _yes_all()
    # Remplacer Q08 par 20h
    responses = [
        ResponseInput("Q08", "FREE_NUMERIC", 20.0) if r.question_code == "Q08" else r
        for r in responses
    ]
    result = compute_scores(QUESTIONS, responses)
    # Gap > 0 mais < 100
    assert 0.0 < result.digital_gap_pct < 100.0


def test_scores_by_category_present() -> None:
    result = compute_scores(QUESTIONS, _yes_all())
    assert set(result.scores_by_category.keys()) == {"FISCALE", "SOCIALE", "CONFORMITE", "DIGITALE"}


def test_compute_digital_gap_all_no() -> None:
    """Gap = 100 % quand toutes les valeurs sont 0 (réponses converties correctement)."""
    response_map: dict[str, ResponseInput] = {}
    for q in QUESTIONS:
        if q.answer_type == "FREE_NUMERIC":
            response_map[q.code] = ResponseInput(q.code, "FREE_NUMERIC", 40.0)
        else:
            response_map[q.code] = ResponseInput(q.code, "NO")
    gap = _compute_digital_gap(QUESTIONS, response_map)
    assert gap == pytest.approx(100.0)


def test_compute_digital_gap_all_yes() -> None:
    """Gap = 0 % quand toutes les valeurs sont 1."""
    response_map = {}
    for q in QUESTIONS:
        if q.answer_type == "FREE_NUMERIC":
            response_map[q.code] = ResponseInput(q.code, "FREE_NUMERIC", 0.0)
        else:
            response_map[q.code] = ResponseInput(q.code, "YES")
    gap = _compute_digital_gap(QUESTIONS, response_map)
    assert gap == pytest.approx(0.0, abs=1e-9)


def test_compute_digital_gap_no_questions() -> None:
    """Sans questions, le gap est 100 % par convention."""
    gap = _compute_digital_gap([], {})
    assert gap == pytest.approx(100.0)


def test_free_numeric_negative_clamped() -> None:
    """Valeur négative (aberrante) est clampée à [0, 1] → résultat = 1.0."""
    result = map_answer_to_value("FREE_NUMERIC", "FREE_NUMERIC", -5.0)
    # min(1.0, max(0.0, 1 - (-5)/40)) = min(1.0, 1.125) = 1.0
    assert result == pytest.approx(1.0)
    assert 0.0 <= result <= 1.0
