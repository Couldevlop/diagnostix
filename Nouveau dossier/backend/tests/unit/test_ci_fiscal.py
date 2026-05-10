"""Tests du module `app.core.ci_fiscal`.

Couvre IGR, CNPS, IFC, FDFP avec ≥ 8 cas paramétrés par fonction comme exigé
dans le CLAUDE.md (§7.6). Les valeurs attendues ont été calculées à la main
à partir des barèmes officiels.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.core.ci_fiscal import (
    CNPS_CEILING_MONTHLY,
    SMIG_MONTHLY,
    compute_cnps,
    compute_fdfp,
    compute_ifc,
    compute_igr,
)


# =============================================================================
# IGR — 8 cas couvrant chaque tranche et les bornes
# =============================================================================
@pytest.mark.parametrize(
    ("revenu", "attendu"),
    [
        (Decimal("0"),         Decimal("0")),                # tranche 1 (0 %)
        (Decimal("75000"),     Decimal("0")),                # borne sup tranche 1
        (Decimal("100000"),    Decimal("4000")),             # 0.16 * (100000-75000) = 4000
        (Decimal("240000"),    Decimal("26400")),            # 0.16 * (240000-75000) = 26400
        (Decimal("500000"),    Decimal("81000")),            # 26400 + 0.21*(500000-240000)
        (Decimal("800000"),    Decimal("144000")),           # 26400 + 0.21*560000
        (Decimal("2400000"),   Decimal("528000")),           # 26400 + 117600 + 0.24*1600000
        (Decimal("10000000"),  Decimal("2736000")),          # ...+0.28*5600000+0.32*2000000
    ],
)
def test_compute_igr(revenu: Decimal, attendu: Decimal) -> None:
    """IGR — vérification des montants par tranche (valeurs calculées manuellement)."""
    resultat = compute_igr(revenu)
    assert resultat == attendu, f"IGR({revenu}) = {resultat}, attendu = {attendu}"


def test_compute_igr_revenu_negatif() -> None:
    with pytest.raises(ValueError, match="négatif"):
        compute_igr(Decimal("-1"))


# =============================================================================
# CNPS — plafond, bornes
# =============================================================================
@pytest.mark.parametrize(
    ("salaire", "base_attendue", "employeur_att", "salarie_att"),
    [
        (Decimal("0"),       Decimal("0"),       Decimal("0"),     Decimal("0")),
        (Decimal("75000"),   Decimal("75000"),   Decimal("7875"),  Decimal("4125")),
        (Decimal("200000"),  Decimal("200000"),  Decimal("21000"), Decimal("11000")),
        (Decimal("500000"),  Decimal("500000"),  Decimal("52500"), Decimal("27500")),
        (Decimal("600000"),  Decimal("600000"),  Decimal("63000"), Decimal("33000")),
        (Decimal("700000"),  Decimal("600000"),  Decimal("63000"), Decimal("33000")),  # plafond atteint
        (Decimal("1500000"), Decimal("600000"),  Decimal("63000"), Decimal("33000")),  # bien au-dessus
        (Decimal("9999999"), Decimal("600000"),  Decimal("63000"), Decimal("33000")),
    ],
)
def test_compute_cnps(
    salaire: Decimal,
    base_attendue: Decimal,
    employeur_att: Decimal,
    salarie_att: Decimal,
) -> None:
    res = compute_cnps(salaire)
    assert res.base_cotisable == base_attendue
    assert res.employer_part == employeur_att
    assert res.employee_part == salarie_att
    assert res.total == employeur_att + salarie_att


def test_compute_cnps_salaire_negatif() -> None:
    with pytest.raises(ValueError):
        compute_cnps(Decimal("-1"))


def test_cnps_ceiling_value() -> None:
    """Le plafond CNPS 2026 est bien de 600 000 FCFA (cf. cahier des charges)."""
    assert CNPS_CEILING_MONTHLY == 600_000


# =============================================================================
# IFC — 8 cas couvrant les 3 tranches
# =============================================================================
@pytest.mark.parametrize(
    ("salaire_moyen", "anciennete", "attendu"),
    [
        (Decimal("300000"), 0,  Decimal("0")),                 # < 1 an
        (Decimal("300000"), 1,  Decimal("90000")),             # 1×30%
        (Decimal("300000"), 5,  Decimal("450000")),            # 5×30%
        (Decimal("300000"), 6,  Decimal("555000")),            # 5×30% + 1×35%
        (Decimal("300000"), 10, Decimal("975000")),            # 5×30% + 5×35%
        (Decimal("300000"), 11, Decimal("1095000")),           # + 1×40%
        (Decimal("500000"), 15, Decimal("2625000")),           # 5×30% + 5×35% + 5×40% × 500k = 5.25 mois
        (Decimal("0"),      10, Decimal("0")),                 # salaire nul
    ],
)
def test_compute_ifc(salaire_moyen: Decimal, anciennete: int, attendu: Decimal) -> None:
    assert compute_ifc(salaire_moyen, anciennete) == attendu


def test_compute_ifc_salaire_negatif() -> None:
    with pytest.raises(ValueError):
        compute_ifc(Decimal("-1"), 5)


def test_compute_ifc_anciennete_negative() -> None:
    with pytest.raises(ValueError):
        compute_ifc(Decimal("300000"), -1)


# =============================================================================
# FDFP
# =============================================================================
@pytest.mark.parametrize(
    ("masse", "attendu"),
    [
        (Decimal("0"),         Decimal("0")),
        (Decimal("1000000"),   Decimal("12000")),
        (Decimal("10000000"),  Decimal("120000")),
        (Decimal("100000000"), Decimal("1200000")),
    ],
)
def test_compute_fdfp(masse: Decimal, attendu: Decimal) -> None:
    assert compute_fdfp(masse) == attendu


def test_compute_fdfp_negatif() -> None:
    with pytest.raises(ValueError):
        compute_fdfp(Decimal("-1"))


def test_smig_value() -> None:
    """Le SMIG en vigueur est bien 75 000 FCFA / mois."""
    assert SMIG_MONTHLY == 75_000
