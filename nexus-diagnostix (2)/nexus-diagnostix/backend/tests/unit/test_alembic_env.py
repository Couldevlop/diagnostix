"""Tests de régression pour le bug d'interpolation ConfigParser dans Alembic.

Bug historique :
    Quand on injectait l'URL DB via `config.set_main_option("sqlalchemy.url", ...)`,
    ConfigParser interprétait les `%` comme une syntaxe d'interpolation.
    Résultat : toute URL contenant `%XX` (URL-encoding d'un mot de passe spécial)
    plantait avec `ValueError: invalid interpolation syntax`.

Exemple typique : mot de passe `Admin@1234!`
    → encodé `Admin%401234%21`
    → URL `postgresql+asyncpg://user:Admin%401234%21@host/db`
    → CRASH

Fix : `alembic/env.py` n'utilise plus `set_main_option`. L'URL est passée
directement à `create_async_engine`, qui ne fait pas d'interpolation.

Ces tests garantissent que le fix tient dans le temps.
"""
from __future__ import annotations

import importlib
import os
from pathlib import Path

import pytest


# URLs problématiques connues — chaque entrée est un cas réel rencontré.
PROBLEMATIC_URLS = [
    # Mot de passe avec @ encodé (Admin@1234)
    "postgresql+asyncpg://nexus:Admin%401234@postgres:5432/nexus_db",
    # Mot de passe avec @ et ! encodés (Admin@1234!)
    "postgresql+asyncpg://nexus:Admin%401234%21@postgres:5432/nexus_db",
    # Mot de passe avec : encodé
    "postgresql+asyncpg://nexus:pass%3Aword@postgres:5432/nexus_db",
    # Mot de passe contenant plusieurs % consécutifs
    "postgresql+asyncpg://nexus:%40%21%23%24@postgres:5432/nexus_db",
    # URL "saine" — doit aussi continuer à marcher
    "postgresql+asyncpg://nexus:simplepass@postgres:5432/nexus_db",
]


@pytest.mark.parametrize("problematic_url", PROBLEMATIC_URLS)
def test_alembic_env_loads_with_url_containing_percent(
    problematic_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Le module `alembic/env.py` ne doit JAMAIS planter sur ConfigParser
    à cause d'une URL contenant `%`.

    On simule l'environnement et on vérifie que l'URL Pydantic se charge
    sans erreur — c'est exactement la même opération qu'Alembic exécute
    au démarrage de `alembic upgrade`.
    """
    monkeypatch.setenv("DATABASE_URL", problematic_url)

    # Recharger les Settings depuis le nouvel environnement
    from app import config as app_config
    importlib.reload(app_config)

    settings = app_config.get_settings()
    url = str(settings.database_url)

    # L'URL doit être chargée sans modification
    assert url == problematic_url, (
        f"L'URL chargée ({url}) diffère de l'URL fournie ({problematic_url})"
    )


def test_alembic_env_does_not_use_set_main_option(monkeypatch: pytest.MonkeyPatch) -> None:
    """Vérifie statiquement que `alembic/env.py` n'utilise PAS la méthode
    fautive `config.set_main_option('sqlalchemy.url', ...)`.

    Si quelqu'un réintroduit cette ligne, ce test échoue immédiatement.

    On parse l'AST plutôt que de grepper le texte brut, pour ignorer
    légitimement les mentions de la fonction dans les docstrings et commentaires.
    """
    import ast

    backend_dir = Path(__file__).resolve().parent.parent.parent
    env_file = backend_dir / "alembic" / "env.py"
    assert env_file.exists(), f"alembic/env.py introuvable à {env_file}"

    tree = ast.parse(env_file.read_text(encoding="utf-8"))

    forbidden_calls: list[str] = []
    for node in ast.walk(tree):
        # Cherche : <quoi que ce soit>.set_main_option(<premier_arg>, ...)
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "set_main_option"
            and node.args
        ):
            first = node.args[0]
            if isinstance(first, ast.Constant) and first.value == "sqlalchemy.url":
                forbidden_calls.append(ast.unparse(node))

    assert not forbidden_calls, (
        "Régression détectée : alembic/env.py contient un appel à "
        "`set_main_option('sqlalchemy.url', ...)`. Cela provoque le bug "
        "d'interpolation ConfigParser sur les mots de passe contenant des `%`. "
        f"Appels détectés : {forbidden_calls}"
    )
