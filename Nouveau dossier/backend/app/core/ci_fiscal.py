"""Barèmes et calculs fiscaux et sociaux applicables en Côte d'Ivoire.

⚠️ Ce module contient les VALEURS DE RÉFÉRENCE par défaut.
Les valeurs effectives utilisées en production sont stockées dans la table
`settings` et chargées dynamiquement, pour permettre à un admin de mettre à
jour la fiscalité (ex. nouveau plafond CNPS) sans redéploiement.

Sources :
- Réforme IGR 2024 (Annexe fiscale au CGI CI).
- Code de prévoyance sociale, taux CNPS 2024-2026.
- Convention Collective Interprofessionnelle de Côte d'Ivoire (IFC).
- Code du Travail CI (heures supplémentaires).
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Final

# =============================================================================
# 1. IGR — Impôt Général sur le Revenu (réforme 2024)
# =============================================================================
# Format : (borne_inf, borne_sup_inclus, taux). `None` pour la dernière borne.
IGR_BRACKETS_2024: Final[list[tuple[int, int | None, Decimal]]] = [
    (0,         75_000,    Decimal("0.00")),
    (75_001,    240_000,   Decimal("0.16")),
    (240_001,   800_000,   Decimal("0.21")),
    (800_001,   2_400_000, Decimal("0.24")),
    (2_400_001, 8_000_000, Decimal("0.28")),
    (8_000_001, None,      Decimal("0.32")),
]


def compute_igr(revenu_imposable_mensuel: Decimal) -> Decimal:
    """Calcule l'IGR mensuel selon le barème progressif 2024.

    Logique : pour un revenu R, on additionne pour chaque tranche
    `(min(R, borne_sup) - (borne_inf - 1)) * taux` si R atteint la tranche.

    Args:
        revenu_imposable_mensuel: revenu imposable en FCFA (positif).

    Returns:
        Montant de l'IGR en FCFA, arrondi au franc le plus proche.
    """
    if revenu_imposable_mensuel < 0:
        raise ValueError("Le revenu imposable ne peut pas être négatif.")

    impot = Decimal("0")
    revenu = revenu_imposable_mensuel

    for borne_inf, borne_sup, taux in IGR_BRACKETS_2024:
        if revenu < borne_inf:
            break
        # `borne_inf` est inclusif → le bas réel de la tranche est `borne_inf - 1` côté
        # cumulé (sauf pour la tranche 0). On considère ici que la tranche commence
        # à `borne_inf` et qu'elle a pour amplitude `borne_sup - borne_inf + 1` FCFA.
        bas = Decimal(borne_inf if borne_inf == 0 else borne_inf - 1)
        haut = Decimal(borne_sup) if borne_sup is not None else revenu
        plafond_effectif = min(revenu, haut)
        amplitude = plafond_effectif - bas
        if amplitude > 0:
            impot += amplitude * taux

    return impot.quantize(Decimal("1"))


# =============================================================================
# 2. CNPS — Caisse Nationale de Prévoyance Sociale
# =============================================================================
CNPS_EMPLOYER_RATE: Final[Decimal] = Decimal("0.105")    # 10,5 %
CNPS_EMPLOYEE_RATE: Final[Decimal] = Decimal("0.055")    #  5,5 %
CNPS_CEILING_MONTHLY: Final[int] = 600_000               # FCFA / mois (2026)


@dataclass(frozen=True)
class CnpsContribution:
    """Résultat d'un calcul de cotisation CNPS."""

    base_cotisable: Decimal
    employer_part: Decimal
    employee_part: Decimal

    @property
    def total(self) -> Decimal:
        return self.employer_part + self.employee_part


def compute_cnps(salaire_brut_mensuel: Decimal) -> CnpsContribution:
    """Calcule les cotisations CNPS (parts employeur et salariale)."""
    if salaire_brut_mensuel < 0:
        raise ValueError("Le salaire brut ne peut pas être négatif.")

    base = min(salaire_brut_mensuel, Decimal(CNPS_CEILING_MONTHLY))
    return CnpsContribution(
        base_cotisable=base,
        employer_part=(base * CNPS_EMPLOYER_RATE).quantize(Decimal("1")),
        employee_part=(base * CNPS_EMPLOYEE_RATE).quantize(Decimal("1")),
    )


# =============================================================================
# 3. IFC — Indemnité de Fin de Carrière (Convention Collective Interpro CI)
# =============================================================================
# Taux du salaire moyen mensuel des 12 derniers mois, par année d'ancienneté.
IFC_RATES: Final[list[tuple[int, int | None, Decimal]]] = [
    (1,  5,    Decimal("0.30")),   # 1 à 5 ans
    (6,  10,   Decimal("0.35")),   # 6 à 10 ans
    (11, None, Decimal("0.40")),   # au-delà de 10 ans
]


def compute_ifc(salaire_moyen_mensuel: Decimal, anciennete_annees: int) -> Decimal:
    """Calcule l'IFC selon la Convention Collective Interprofessionnelle CI.

    L'IFC est cumulative année par année selon les taux applicables.
    """
    if salaire_moyen_mensuel < 0:
        raise ValueError("Le salaire moyen ne peut pas être négatif.")
    if anciennete_annees < 0:
        raise ValueError("L'ancienneté ne peut pas être négative.")
    if anciennete_annees < 1:
        return Decimal("0")

    montant = Decimal("0")
    for borne_inf, borne_sup, taux in IFC_RATES:
        if anciennete_annees < borne_inf:
            break
        plafond = borne_sup if borne_sup is not None else anciennete_annees
        annees_dans_tranche = min(anciennete_annees, plafond) - (borne_inf - 1)
        if annees_dans_tranche > 0:
            montant += salaire_moyen_mensuel * taux * annees_dans_tranche

    return montant.quantize(Decimal("1"))


# =============================================================================
# 4. Heures supplémentaires (Code du Travail CI)
# =============================================================================
HEURES_SUP_PLAFOND_HEBDO: Final[int] = 15
HEURES_SUP_PLAFOND_ANNUEL: Final[int] = 75

HEURES_SUP_MAJORATIONS: Final[dict[str, Decimal]] = {
    "j_ouvrable_15pct": Decimal("0.15"),   # 41e à 46e h
    "j_ouvrable_50pct": Decimal("0.50"),   # au-delà de la 46e h
    "nuit_ouvrable":    Decimal("0.75"),
    "j_repos_jour":     Decimal("0.75"),
    "j_repos_nuit":     Decimal("1.00"),
}


# =============================================================================
# 5. FDFP — Fonds de Développement de la Formation Professionnelle
# =============================================================================
FDFP_RATE: Final[Decimal] = Decimal("0.012")   # 1,2 % de la masse salariale brute


def compute_fdfp(masse_salariale_brute: Decimal) -> Decimal:
    """Calcule la cotisation FDFP."""
    if masse_salariale_brute < 0:
        raise ValueError("La masse salariale ne peut pas être négative.")
    return (masse_salariale_brute * FDFP_RATE).quantize(Decimal("1"))


# =============================================================================
# 6. SMIG (Salaire Minimum Interprofessionnel Garanti)
# =============================================================================
SMIG_MONTHLY: Final[int] = 75_000   # FCFA / mois (en vigueur 2024-2026)
