"""Service IA — wrapper Claude API avec validation Pydantic (§8.5 du CLAUDE.md).

Pipeline :
1. Construit le prompt à partir des résultats des étages 1-3.
2. Appel Claude API (claude-opus-4-7, temperature=0.3, max_tokens=2000).
3. Validation Pydantic stricte de la réponse JSON.
4. 1 retry avec prompt correctif en cas d'échec de validation.
5. Fallback statique si le retry échoue ou si l'API est indisponible.

Cache Redis : clé = SHA-256 des inputs sérialisés → évite les appels redondants.
"""
from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

import anthropic
from pydantic import BaseModel, Field, ValidationError, model_validator

from app.core.prompts.expert_system import CORRECTION_PROMPT, EXPERT_SYSTEM_PROMPT

logger = logging.getLogger("app.ai_service")


# ---------------------------------------------------------------------------
# Schéma de validation de la réponse Claude
# ---------------------------------------------------------------------------
class Recommendation(BaseModel):
    priority: int = Field(ge=1, le=3)
    title: str
    description: str
    expected_gain_fcfa: int = Field(ge=0)
    implementation_weeks: int = Field(ge=1)
    nexusrh_module: str


class AIAnalysis(BaseModel):
    executive_summary: str
    risk_narrative: str
    digital_gap_narrative: str
    recommendations: list[Recommendation] = Field(min_length=3, max_length=3)
    key_takeaway: str

    @model_validator(mode="after")
    def _check_recommendation_priorities(self) -> "AIAnalysis":
        priorities = [r.priority for r in self.recommendations]
        if sorted(priorities) != [1, 2, 3]:
            raise ValueError("Les recommandations doivent avoir les priorités 1, 2 et 3.")
        return self


# ---------------------------------------------------------------------------
# Fallback statique
# ---------------------------------------------------------------------------
def _build_fallback(
    global_score: float,
    maturity_level: str,
    financial_exposure: int,
) -> AIAnalysis:
    """Retourne une analyse générique quand l'API Claude est indisponible."""
    level_label = {
        "CRITIQUE":  "critique",
        "EMERGENT":  "émergent",
        "STRUCTURE": "en cours de structuration",
        "OPTIMISE":  "optimisé",
        "IA_NATIVE": "IA-Native",
    }.get(maturity_level, "en développement")

    return AIAnalysis(
        executive_summary=(
            f"Votre organisation présente un niveau de maturité digitale RH {level_label} "
            f"avec un score global de {global_score:.1f}/100. "
            f"Une exposition financière estimée à {financial_exposure:,} FCFA "
            "nécessite une action immédiate sur vos risques de conformité."
        ),
        risk_narrative=(
            "Des risques de redressement fiscal et social ont été identifiés. "
            "Un audit immédiat de vos processus de paie et de vos déclarations "
            "CNPS est fortement recommandé pour limiter votre exposition."
        ),
        digital_gap_narrative=(
            "Votre écart par rapport au standard IA-Native représente une opportunité "
            "de modernisation. Des solutions SaaS RH adaptées au contexte ivoirien "
            "peuvent combler ce gap en 3 à 6 mois."
        ),
        recommendations=[
            Recommendation(
                priority=1,
                title="Mise en conformité IGR 2024",
                description="Mettre à jour votre logiciel de paie pour intégrer la réforme IGR 2024.",
                expected_gain_fcfa=int(financial_exposure * 0.4),
                implementation_weeks=4,
                nexusrh_module="NexusRH Paie CI",
            ),
            Recommendation(
                priority=2,
                title="Automatisation des déclarations CNPS",
                description="Automatiser la génération des DISA pour éliminer les risques de pénalités.",
                expected_gain_fcfa=int(financial_exposure * 0.3),
                implementation_weeks=8,
                nexusrh_module="NexusRH Déclarations",
            ),
            Recommendation(
                priority=3,
                title="Déploiement du portail employé",
                description="Digitaliser les bulletins et les demandes RH pour réduire les coûts opérationnels.",
                expected_gain_fcfa=int(financial_exposure * 0.2),
                implementation_weeks=12,
                nexusrh_module="NexusRH Self-Service",
            ),
        ],
        key_takeaway=(
            "Contactez NexusRH dès aujourd'hui pour une démo personnalisée "
            "et commencez votre transformation digitale RH en toute conformité."
        ),
    )


# ---------------------------------------------------------------------------
# Service principal
# ---------------------------------------------------------------------------
def _build_payload(
    global_score: float,
    maturity_level: str,
    scores_by_category: dict[str, float],
    risks_detected: list[dict[str, Any]],
    financial_exposure: int,
    non_compliance_proba: float | None,
    digital_gap_pct: float,
) -> str:
    """Remplit le template du prompt système avec les données calculées."""
    return EXPERT_SYSTEM_PROMPT.format(
        global_score=round(global_score, 1),
        maturity_level=maturity_level,
        scores_by_category=json.dumps(scores_by_category, ensure_ascii=False),
        risks_detected=json.dumps(risks_detected, ensure_ascii=False),
        financial_exposure=financial_exposure,
        non_compliance_proba=(
            f"{non_compliance_proba:.1%}" if non_compliance_proba is not None else "Donnée insuffisante"
        ),
        digital_gap_pct=round(digital_gap_pct, 1),
    )


def _parse_ai_response(text: str) -> AIAnalysis:
    """Extrait et valide le JSON de la réponse Claude."""
    # Essai de parse direct
    stripped = text.strip()
    # Si Claude a ajouté des backticks markdown, on les retire
    if stripped.startswith("```"):
        lines = stripped.split("\n")
        stripped = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    data = json.loads(stripped)
    return AIAnalysis.model_validate(data)


def get_ai_analysis(
    *,
    global_score: float,
    maturity_level: str,
    scores_by_category: dict[str, float],
    risks_detected: list[dict[str, Any]],
    financial_exposure: int,
    non_compliance_proba: float | None,
    digital_gap_pct: float,
    redis_client: Any = None,
    anthropic_client: anthropic.Anthropic | None = None,
    model: str = "claude-opus-4-7",
    max_tokens: int = 2000,
    temperature: float = 0.3,
    timeout: float = 30.0,
) -> AIAnalysis:
    """Orchestre l'appel Claude avec cache, retry et fallback.

    Args:
        redis_client:     Client Redis optionnel pour le cache.
        anthropic_client: Client Anthropic (injecté pour les tests).
    """
    prompt_text = _build_payload(
        global_score, maturity_level, scores_by_category,
        risks_detected, financial_exposure, non_compliance_proba, digital_gap_pct,
    )

    # --- Cache Redis ---
    cache_key: str | None = None
    if redis_client is not None:
        cache_key = "ai:" + hashlib.sha256(prompt_text.encode()).hexdigest()
        try:
            cached = redis_client.get(cache_key)
            if cached:
                data = json.loads(cached)
                return AIAnalysis.model_validate(data)
        except Exception:   # noqa: BLE001
            logger.warning("Redis cache read failed — ignoring")

    # --- Appel API avec retry ---
    client = anthropic_client or anthropic.Anthropic()
    messages: list[dict[str, str]] = [{"role": "user", "content": prompt_text}]

    for attempt in range(2):
        try:
            resp = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages,  # type: ignore[arg-type]
            )
            raw_text = resp.content[0].text
            analysis = _parse_ai_response(raw_text)

            # Mise en cache Redis
            if redis_client is not None and cache_key:
                try:
                    redis_client.setex(cache_key, 3600 * 24, analysis.model_dump_json())
                except Exception:  # noqa: BLE001
                    pass

            logger.info(
                "ai_analysis.success",
                attempt=attempt,
                input_tokens=resp.usage.input_tokens,
                output_tokens=resp.usage.output_tokens,
            )
            return analysis

        except (json.JSONDecodeError, ValidationError) as exc:
            if attempt == 0:
                # Retry avec prompt correctif
                messages = [
                    {"role": "user", "content": prompt_text},
                    {"role": "assistant", "content": raw_text if "raw_text" in dir() else ""},
                    {"role": "user", "content": CORRECTION_PROMPT},
                ]
                logger.warning("ai_analysis.parse_error_retry: %s", exc)
            else:
                logger.error("ai_analysis.parse_error_fallback: %s", exc)
                break

        except anthropic.APIError as exc:
            logger.error("ai_analysis.api_error_fallback: %s", exc)
            break

    # --- Fallback statique ---
    logger.warning("ai_analysis.using_fallback")
    return _build_fallback(global_score, maturity_level, financial_exposure)
