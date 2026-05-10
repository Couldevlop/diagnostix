"""Données de seed initiales — questions, settings, admin.

À exécuter après `alembic upgrade head` :
    docker compose exec backend python -m app.scripts.seed_initial_data

Idempotent : peut être exécuté plusieurs fois sans dupliquer les données.
"""
from __future__ import annotations

import asyncio
import secrets
import string
from decimal import Decimal
from typing import Any

import structlog
from passlib.context import CryptContext
from sqlalchemy import select

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models import Question, Setting, User
from app.models.question import AnswerType, QuestionCategory
from app.models.user import UserRole

logger = structlog.get_logger("app.scripts.seed")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# =============================================================================
# Les 20 questions du diagnostic — Annexe 2 du cahier des charges
# =============================================================================
QUESTIONS_DATA: list[dict[str, Any]] = [
    {
        "code": "Q01", "order": 1, "weight": 10,
        "category": QuestionCategory.FISCALE.value,
        "answer_type": AnswerType.YES_NO_PARTIAL.value,
        "label": "Vos bulletins de paie intègrent-ils la réforme IGR 2024 ?",
        "help_text": "La réforme fiscale 2024 a modifié le barème de l'IGR. Vérifiez que votre logiciel a été mis à jour.",
    },
    {
        "code": "Q02", "order": 2, "weight": 10,
        "category": QuestionCategory.SOCIALE.value,
        "answer_type": AnswerType.YES_NO_MANUAL.value,
        "label": "Le calcul de vos IFC est-il automatisé selon la Convention Collective ?",
        "help_text": "L'IFC (Indemnité de Fin de Carrière) suit des taux progressifs : 30 % de 1 à 5 ans, 35 % de 6 à 10 ans, 40 % au-delà.",
    },
    {
        "code": "Q03", "order": 3, "weight": 5,
        "category": QuestionCategory.SOCIALE.value,
        "answer_type": AnswerType.YES_NO.value,
        "label": "Le système bloque-t-il les dépassements d'heures supplémentaires au-delà du plafond légal ?",
        "help_text": "Plafond hebdomadaire : 15 h. Plafond annuel : 75 h sans autorisation de l'Inspection du Travail.",
    },
    {
        "code": "Q04", "order": 4, "weight": 10,
        "category": QuestionCategory.CONFORMITE.value,
        "answer_type": AnswerType.YES_NO.value,
        "label": "Disposez-vous d'un historique d'audit modifiable uniquement par l'administrateur ?",
        "help_text": "Un journal d'audit immuable est exigé pour la traçabilité réglementaire et les contrôles.",
    },
    {
        "code": "Q05", "order": 5, "weight": 5,
        "category": QuestionCategory.DIGITALE.value,
        "answer_type": AnswerType.YES_NO_PARTIAL.value,
        "label": "Vos DISA sont-elles générées automatiquement sans retraitement Excel ?",
        "help_text": "La DISA (Déclaration Individuelle des Salaires Annuels) est obligatoire auprès de la CNPS.",
    },
    {
        "code": "Q06", "order": 6, "weight": 5,
        "category": QuestionCategory.DIGITALE.value,
        "answer_type": AnswerType.YES_NO.value,
        "label": "Délai moyen de sortie de paie : moins de 2 jours après la fin du mois ?",
        "help_text": None,
    },
    {
        "code": "Q07", "order": 7, "weight": 5,
        "category": QuestionCategory.DIGITALE.value,
        "answer_type": AnswerType.YES_NO.value,
        "label": "Vos processus de validation de congés sont-ils 100 % sans papier ?",
        "help_text": None,
    },
    {
        "code": "Q08", "order": 8, "weight": 10,
        "category": QuestionCategory.DIGITALE.value,
        "answer_type": AnswerType.FREE_NUMERIC.value,
        "label": "Temps hebdomadaire perdu en saisie de données RH (en heures) ?",
        "help_text": "Estimez le total hebdomadaire pour l'équipe RH (saisie, ressaisie, copier-coller).",
    },
    {
        "code": "Q09", "order": 9, "weight": 5,
        "category": QuestionCategory.DIGITALE.value,
        "answer_type": AnswerType.YES_NO.value,
        "label": "Les employés reçoivent-ils leurs bulletins sur un portail sécurisé ?",
        "help_text": None,
    },
    {
        "code": "Q10", "order": 10, "weight": 5,
        "category": QuestionCategory.SOCIALE.value,
        "answer_type": AnswerType.YES_NO.value,
        "label": "Les prêts et avances sont-ils déduits automatiquement en paie ?",
        "help_text": None,
    },
    {
        "code": "Q11", "order": 11, "weight": 10,
        "category": QuestionCategory.DIGITALE.value,
        "answer_type": AnswerType.YES_NO.value,
        "label": "Générez-vous votre bilan social en un seul clic ?",
        "help_text": "Le bilan social annuel est une obligation pour les entreprises de plus de 300 salariés.",
    },
    {
        "code": "Q12", "order": 12, "weight": 5,
        "category": QuestionCategory.DIGITALE.value,
        "answer_type": AnswerType.YES_NO.value,
        "label": "Recevez-vous des alertes 30 jours avant la fin d'un CDD ou d'une période d'essai ?",
        "help_text": None,
    },
    {
        "code": "Q13", "order": 13, "weight": 5,
        "category": QuestionCategory.DIGITALE.value,
        "answer_type": AnswerType.YES_NO.value,
        "label": "Avez-vous une cartographie digitale des compétences critiques ?",
        "help_text": None,
    },
    {
        "code": "Q14", "order": 14, "weight": 5,
        "category": QuestionCategory.DIGITALE.value,
        "answer_type": AnswerType.YES_NO.value,
        "label": "Vos entretiens annuels sont-ils liés numériquement aux objectifs ?",
        "help_text": None,
    },
    {
        "code": "Q15", "order": 15, "weight": 5,
        "category": QuestionCategory.DIGITALE.value,
        "answer_type": AnswerType.YES_NO.value,
        "label": "Suivez-vous l'absentéisme en temps réel par département ?",
        "help_text": None,
    },
    {
        "code": "Q16", "order": 16, "weight": 10,
        "category": QuestionCategory.DIGITALE.value,
        "answer_type": AnswerType.YES_NO.value,
        "label": "Votre système peut-il prédire les risques de turnover ?",
        "help_text": "Les outils modernes utilisent le machine learning pour anticiper les départs à 12 mois.",
    },
    {
        "code": "Q17", "order": 17, "weight": 5,
        "category": QuestionCategory.DIGITALE.value,
        "answer_type": AnswerType.YES_NO.value,
        "label": "Avez-vous un Assistant IA pour les questions RH récurrentes ?",
        "help_text": None,
    },
    {
        "code": "Q18", "order": 18, "weight": 10,
        "category": QuestionCategory.DIGITALE.value,
        "answer_type": AnswerType.YES_NO.value,
        "label": "Simulez-vous l'impact d'une hausse de masse salariale en 10 secondes ?",
        "help_text": None,
    },
    {
        "code": "Q19", "order": 19, "weight": 5,
        "category": QuestionCategory.DIGITALE.value,
        "answer_type": AnswerType.YES_NO.value,
        "label": "Gérez-vous plusieurs sites ou pays sur une interface unique ?",
        "help_text": None,
    },
    {
        "code": "Q20", "order": 20, "weight": 10,
        "category": QuestionCategory.CONFORMITE.value,
        "answer_type": AnswerType.YES_NO.value,
        "label": "Votre base de données est-elle déclarée conforme à la loi ARTCI ?",
        "help_text": "La Loi 2013-450 impose une déclaration auprès de l'ARTCI pour tout traitement de données personnelles.",
    },
]


# =============================================================================
# Paramètres applicatifs initiaux
# =============================================================================
def _decimal(value: str) -> str:
    """Conserve les Decimal en string dans JSON pour préserver la précision."""
    return str(Decimal(value))


SETTINGS_DATA: list[dict[str, Any]] = [
    {
        "key": "cnps_employer_rate",
        "value": _decimal("0.105"),
        "description": "Taux CNPS part employeur (10,5 %).",
    },
    {
        "key": "cnps_employee_rate",
        "value": _decimal("0.055"),
        "description": "Taux CNPS part salariale (5,5 %).",
    },
    {
        "key": "cnps_ceiling_monthly",
        "value": 600_000,
        "description": "Plafond mensuel des cotisations CNPS en FCFA (2026).",
    },
    {
        "key": "smig_monthly",
        "value": 75_000,
        "description": "SMIG mensuel en FCFA.",
    },
    {
        "key": "fdfp_rate",
        "value": _decimal("0.012"),
        "description": "Taux FDFP (1,2 % de la masse salariale brute).",
    },
    {
        "key": "igr_brackets_2024",
        "value": [
            {"min": 0,         "max": 75_000,    "rate": _decimal("0.00")},
            {"min": 75_001,    "max": 240_000,   "rate": _decimal("0.16")},
            {"min": 240_001,   "max": 800_000,   "rate": _decimal("0.21")},
            {"min": 800_001,   "max": 2_400_000, "rate": _decimal("0.24")},
            {"min": 2_400_001, "max": 8_000_000, "rate": _decimal("0.28")},
            {"min": 8_000_001, "max": None,      "rate": _decimal("0.32")},
        ],
        "description": "Barème IGR — réforme fiscale 2024 (CGI Côte d'Ivoire).",
    },
]


def _generate_password(length: int = 16) -> str:
    """Génère un mot de passe robuste cryptographiquement aléatoire."""
    alphabet = string.ascii_letters + string.digits + "@#$%&*+="
    return "".join(secrets.choice(alphabet) for _ in range(length))


async def seed_questions(session) -> int:  # type: ignore[no-untyped-def]
    """Insère les 20 questions si elles n'existent pas déjà."""
    inserted = 0
    for data in QUESTIONS_DATA:
        result = await session.execute(select(Question).where(Question.code == data["code"]))
        if result.scalar_one_or_none() is None:
            session.add(Question(**data))
            inserted += 1
    await session.flush()
    return inserted


async def seed_settings(session) -> int:  # type: ignore[no-untyped-def]
    """Insère les settings de référence."""
    inserted = 0
    for data in SETTINGS_DATA:
        result = await session.execute(select(Setting).where(Setting.key == data["key"]))
        if result.scalar_one_or_none() is None:
            session.add(Setting(**data))
            inserted += 1
    await session.flush()
    return inserted


async def seed_admin(session) -> tuple[bool, str | None]:  # type: ignore[no-untyped-def]
    """Crée l'admin initial si absent. Retourne (créé, mot_de_passe_en_clair)."""
    settings_app = get_settings()
    email = settings_app.initial_admin_email

    result = await session.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none() is not None:
        return False, None

    plain_password = (
        settings_app.initial_admin_password.get_secret_value()
        or _generate_password()
    )
    user = User(
        email=email,
        password_hash=pwd_context.hash(plain_password),
        role=UserRole.SUPERADMIN.value,
        is_active=True,
    )
    session.add(user)
    await session.flush()
    return True, plain_password


async def seed_all() -> None:
    """Point d'entrée principal du seed."""
    async with AsyncSessionLocal() as session:
        async with session.begin():
            n_questions = await seed_questions(session)
            n_settings = await seed_settings(session)
            admin_created, admin_password = await seed_admin(session)

        logger.info(
            "seed.completed",
            questions_inserted=n_questions,
            settings_inserted=n_settings,
            admin_created=admin_created,
        )

        if admin_created and admin_password:
            print("=" * 70)
            print("⚠️  COMPTE ADMIN INITIAL CRÉÉ — NOTEZ CE MOT DE PASSE :")
            print(f"    Email    : {get_settings().initial_admin_email}")
            print(f"    Password : {admin_password}")
            print("    Changez ce mot de passe dès la première connexion.")
            print("=" * 70)


if __name__ == "__main__":
    asyncio.run(seed_all())
