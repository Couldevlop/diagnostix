"""Tests du moteur de risques (app.services.risk_engine).

Couverture : 100 % — chaque règle testée individuellement, cas cumulatifs,
bornes du risk_score.
"""
from __future__ import annotations

import pytest

from app.services.risk_engine import (
    RiskContext,
    RiskResult,
    SEVERITY_WEIGHTS,
    compute_risks,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _all_no(effectif: int = 10) -> RiskContext:
    """Toutes les réponses = NO → tous les risques déclenchés."""
    return RiskContext(
        responses_by_code={
            "Q01": "NO", "Q02": "NO", "Q03": "NO",
            "Q04": "NO", "Q05": "NO", "Q20": "NO",
        },
        effectif=effectif,
    )


def _all_ok() -> RiskContext:
    """Réponses idéales → aucun risque."""
    return RiskContext(
        responses_by_code={
            "Q01": "YES", "Q02": "YES", "Q03": "YES",
            "Q04": "YES", "Q05": "YES", "Q20": "YES",
        },
        effectif=10,
    )


# ---------------------------------------------------------------------------
# Cas sans risque
# ---------------------------------------------------------------------------
def test_no_risk_when_all_ok() -> None:
    result = compute_risks(_all_ok())
    assert result.detected_risks == []
    assert result.risk_score == 0.0
    assert result.financial_exposure == 0
    assert result.triggered_codes == []


# ---------------------------------------------------------------------------
# Chaque règle isolément
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("q_code", "answer", "risk_code", "severity"),
    [
        ("Q01", "NO",      "R-FISC-01", "HIGH"),
        ("Q01", "PARTIAL", "R-FISC-01", "HIGH"),   # ≠ YES déclenche aussi
        ("Q02", "MANUAL",  "R-SOC-01",  "HIGH"),
        ("Q03", "NO",      "R-SOC-02",  "MEDIUM"),
        ("Q04", "NO",      "R-CONF-01", "CRITICAL"),
        ("Q05", "NO",      "R-FISC-02", "HIGH"),
        ("Q05", "PARTIAL", "R-FISC-02", "HIGH"),   # ≠ YES
        ("Q20", "NO",      "R-CONF-02", "CRITICAL"),
    ],
)
def test_single_rule_triggered(
    q_code: str, answer: str, risk_code: str, severity: str
) -> None:
    base = {"Q01": "YES", "Q02": "YES", "Q03": "YES", "Q04": "YES", "Q05": "YES", "Q20": "YES"}
    base[q_code] = answer
    result = compute_risks(RiskContext(responses_by_code=base, effectif=10))
    codes = [r.code for r in result.detected_risks]
    assert risk_code in codes
    risk = next(r for r in result.detected_risks if r.code == risk_code)
    assert risk.severity == severity


# ---------------------------------------------------------------------------
# Impact financier
# ---------------------------------------------------------------------------
def test_r_fisc01_impact_proportional_to_effectif() -> None:
    """R-FISC-01 = effectif × SMIG × 2.5 × 0.08."""
    ctx = RiskContext({"Q01": "NO"}, effectif=20, smig_monthly=75_000)
    result = compute_risks(ctx)
    risk = next(r for r in result.detected_risks if r.code == "R-FISC-01")
    expected = int(20 * 75_000 * 2.5 * 0.08)
    assert risk.fcfa_impact == expected


def test_r_soc01_impact() -> None:
    """R-SOC-01 = effectif × 1_500_000."""
    ctx = RiskContext({"Q02": "MANUAL"}, effectif=5)
    result = compute_risks(ctx)
    risk = next(r for r in result.detected_risks if r.code == "R-SOC-01")
    assert risk.fcfa_impact == 5 * 1_500_000


def test_r_soc02_impact() -> None:
    """R-SOC-02 = effectif × 200_000."""
    ctx = RiskContext({"Q03": "NO"}, effectif=8)
    result = compute_risks(ctx)
    risk = next(r for r in result.detected_risks if r.code == "R-SOC-02")
    assert risk.fcfa_impact == 8 * 200_000


def test_r_conf01_impact_forfaitaire() -> None:
    """R-CONF-01 = 5_000_000 forfaitaire."""
    ctx = RiskContext({"Q04": "NO"}, effectif=1)
    result = compute_risks(ctx)
    risk = next(r for r in result.detected_risks if r.code == "R-CONF-01")
    assert risk.fcfa_impact == 5_000_000


def test_r_fisc02_impact() -> None:
    """R-FISC-02 = effectif × 50_000 × 12."""
    ctx = RiskContext({"Q05": "NO"}, effectif=10)
    result = compute_risks(ctx)
    risk = next(r for r in result.detected_risks if r.code == "R-FISC-02")
    assert risk.fcfa_impact == 10 * 50_000 * 12


def test_r_conf02_impact_borne_basse() -> None:
    """R-CONF-02 = 3_000_000 (borne basse)."""
    ctx = RiskContext({"Q20": "NO"}, effectif=1)
    result = compute_risks(ctx)
    risk = next(r for r in result.detected_risks if r.code == "R-CONF-02")
    assert risk.fcfa_impact == 3_000_000


# ---------------------------------------------------------------------------
# Risk score et plafonnement
# ---------------------------------------------------------------------------
def test_risk_score_sum_of_severity_weights() -> None:
    """risk_score = somme des poids de sévérité (MEDIUM + CRITICAL = 65)."""
    # Q01=YES et Q05=YES pour éviter de déclencher R-FISC-01 et R-FISC-02
    ctx = RiskContext(
        {"Q01": "YES", "Q02": "YES", "Q03": "NO", "Q04": "NO", "Q05": "YES", "Q20": "YES"},
        effectif=10,
    )
    result = compute_risks(ctx)
    expected = min(100.0, float(SEVERITY_WEIGHTS["MEDIUM"] + SEVERITY_WEIGHTS["CRITICAL"]))
    assert result.risk_score == expected


def test_risk_score_capped_at_100() -> None:
    """Tous les risques cumulés → risk_score plafonné à 100."""
    result = compute_risks(_all_no(effectif=10))
    assert result.risk_score == 100.0


def test_risk_score_single_high() -> None:
    """Un seul risque HIGH (R-FISC-01) → risk_score = 30."""
    # Fournir Q05=YES pour ne pas déclencher R-FISC-02 en même temps
    ctx = RiskContext(
        {"Q01": "NO", "Q02": "YES", "Q03": "YES", "Q04": "YES", "Q05": "YES", "Q20": "YES"},
        effectif=10,
    )
    result = compute_risks(ctx)
    assert result.risk_score == float(SEVERITY_WEIGHTS["HIGH"])


def test_financial_exposure_cumulative() -> None:
    """L'exposition totale est la somme des impacts individuels."""
    result = compute_risks(_all_no(effectif=10))
    total_expected = sum(r.fcfa_impact for r in result.detected_risks)
    assert result.financial_exposure == total_expected


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------
def test_empty_responses_no_risk() -> None:
    """Aucune réponse fournie → aucun risque (les conditions ne sont pas remplies)."""
    ctx = RiskContext(responses_by_code={}, effectif=10)
    result = compute_risks(ctx)
    # Q02 absent (get → None ≠ "MANUAL" → pas de R-SOC-01)
    # Q03 absent (get → None ≠ "NO" → pas de R-SOC-02)
    # Q04 absent (get → None ≠ "NO" → pas de R-CONF-01)
    # Q20 absent (get → None ≠ "NO" → pas de R-CONF-02)
    # Q01 absent (get → None ≠ "YES" → R-FISC-01 déclenché !)
    # Q05 absent (get → None ≠ "YES" → R-FISC-02 déclenché !)
    triggered = [r.code for r in result.detected_risks]
    assert "R-FISC-01" in triggered
    assert "R-FISC-02" in triggered
    assert "R-SOC-01" not in triggered
    assert "R-CONF-01" not in triggered


def test_effectif_minimum_1() -> None:
    """Même avec effectif=0, le calcul utilise max(1, effectif) = 1."""
    ctx = RiskContext({"Q04": "NO"}, effectif=0)
    result = compute_risks(ctx)
    risk = next(r for r in result.detected_risks if r.code == "R-CONF-01")
    assert risk.fcfa_impact == 5_000_000  # forfaitaire, pas lié à l'effectif


def test_result_is_frozen() -> None:
    result = compute_risks(_all_ok())
    with pytest.raises((AttributeError, TypeError)):
        result.risk_score = 50.0  # type: ignore[misc]


def test_triggered_codes_match_detected_risks() -> None:
    result = compute_risks(_all_no())
    assert result.triggered_codes == [r.code for r in result.detected_risks]
