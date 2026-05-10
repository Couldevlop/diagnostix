"""Moteur de calcul de risques et d'exposition financière (§8.3 du CLAUDE.md).

Applique des règles déterministes basées sur les réponses pour identifier
les risques réglementaires et estimer l'exposition en FCFA.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

from app.core.ci_fiscal import SMIG_MONTHLY

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
SEVERITY_WEIGHTS: Final[dict[str, int]] = {
    "LOW": 5,
    "MEDIUM": 15,
    "HIGH": 30,
    "CRITICAL": 50,
}

# Proxy conservateur pour estimer la masse salariale si non connue
SALARY_MASS_MULTIPLIER: Final[float] = 2.5


# ---------------------------------------------------------------------------
# Structures
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class DetectedRisk:
    """Un risque réglementaire identifié."""

    code: str
    title: str
    severity: str
    fcfa_impact: int
    question_code: str


@dataclass
class RiskContext:
    """Contexte d'entrée du moteur de risques."""

    responses_by_code: dict[str, str]   # code question → valeur de réponse
    effectif: int = 10
    smig_monthly: int = SMIG_MONTHLY    # peut être surchargé via settings BDD


@dataclass(frozen=True)
class RiskResult:
    """Résultat du calcul de risques."""

    detected_risks: list[DetectedRisk]
    risk_score: float                   # 0–100
    financial_exposure: int             # FCFA total
    triggered_codes: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Calcul principal
# ---------------------------------------------------------------------------
def compute_risks(ctx: RiskContext) -> RiskResult:
    """Applique les règles de risque et retourne l'exposition totale.

    Les règles sont celles du CLAUDE.md §8.3. Chaque règle est indépendante ;
    plusieurs peuvent se cumuler.
    """
    r = ctx.responses_by_code
    effectif = max(1, ctx.effectif)
    masse = effectif * ctx.smig_monthly * SALARY_MASS_MULTIPLIER

    detected: list[DetectedRisk] = []

    # R-FISC-01 : Q01 ≠ YES → redressement IGR estimé à 8 % de la masse salariale
    if r.get("Q01") != "YES":
        detected.append(DetectedRisk(
            code="R-FISC-01",
            title="Réforme IGR 2024 non intégrée — risque de redressement fiscal",
            severity="HIGH",
            fcfa_impact=int(masse * 0.08),
            question_code="Q01",
        ))

    # R-SOC-01 : Q02 = MANUAL → IFC calculée à la main, forte probabilité d'erreur
    if r.get("Q02") == "MANUAL":
        detected.append(DetectedRisk(
            code="R-SOC-01",
            title="IFC calculée manuellement — risque d'erreur de calcul CNPS",
            severity="HIGH",
            fcfa_impact=effectif * 1_500_000,
            question_code="Q02",
        ))

    # R-SOC-02 : Q03 = NO → dépassements d'heures supplémentaires non bloqués
    if r.get("Q03") == "NO":
        detected.append(DetectedRisk(
            code="R-SOC-02",
            title="Dépassements d'heures supplémentaires légales non contrôlés",
            severity="MEDIUM",
            fcfa_impact=effectif * 200_000,
            question_code="Q03",
        ))

    # R-CONF-01 : Q04 = NO → absence de journal d'audit — audit irrecevable
    if r.get("Q04") == "NO":
        detected.append(DetectedRisk(
            code="R-CONF-01",
            title="Journal d'audit absent — contrôle CNPS/DGI irrecevable",
            severity="CRITICAL",
            fcfa_impact=5_000_000,
            question_code="Q04",
        ))

    # R-FISC-02 : Q05 ≠ YES → DISA non conformes ou avec retraitements manuels
    if r.get("Q05") != "YES":
        detected.append(DetectedRisk(
            code="R-FISC-02",
            title="DISA non conformes — risque de pénalités CNPS",
            severity="HIGH",
            fcfa_impact=effectif * 50_000 * 12,
            question_code="Q05",
        ))

    # R-CONF-02 : Q20 = NO → base de données non déclarée ARTCI
    if r.get("Q20") == "NO":
        detected.append(DetectedRisk(
            code="R-CONF-02",
            title="Base de données non déclarée ARTCI — sanction possible",
            severity="CRITICAL",
            fcfa_impact=3_000_000,   # borne basse (jusqu'à 50 M selon sévérité)
            question_code="Q20",
        ))

    risk_score = min(
        100.0,
        float(sum(SEVERITY_WEIGHTS[d.severity] for d in detected)),
    )
    financial_exposure = sum(d.fcfa_impact for d in detected)
    triggered_codes = [d.code for d in detected]

    return RiskResult(
        detected_risks=detected,
        risk_score=round(risk_score, 2),
        financial_exposure=financial_exposure,
        triggered_codes=triggered_codes,
    )
