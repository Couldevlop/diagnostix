"""Environnement Alembic pour migrations asynchrones SQLAlchemy 2.

Note importante :
- L'URL de la BDD est injectée via `create_async_engine(DATABASE_URL)`
  directement, **sans passer par ConfigParser**.

  Pourquoi ? `config.set_main_option("sqlalchemy.url", ...)` (méthode classique)
  passe par `ConfigParser` qui utilise `BasicInterpolation` : il interprète le
  caractère `%` comme une syntaxe de variable. Or les URLs de connexion
  contiennent souvent `%XX` (URL-encoding des caractères spéciaux dans les
  mots de passe : `@` → `%40`, `:` → `%3A`, `!` → `%21`, etc.).

  Exemple qui plante : `postgresql://user:pass%40word@host/db`
  → ConfigParser voit `%40` et lève `ValueError: invalid interpolation syntax`.

  Cette implémentation évite complètement le ConfigParser pour l'URL.
"""
from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.config import get_settings
from app.database import Base

# importer tous les modèles pour qu'ils soient visibles d'Alembic
import app.models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Récupérer l'URL depuis Pydantic Settings.
# /!\ On NE l'injecte PAS dans le ConfigParser pour éviter les conflits
# d'interpolation avec les caractères '%' présents dans les URLs encodées.
settings = get_settings()
DATABASE_URL = str(settings.database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Génération SQL sans connexion (mode offline).

    En offline, on alimente directement `context.configure(url=...)` avec
    l'URL Pydantic — ConfigParser n'est pas impliqué.
    """
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Crée un engine async depuis l'URL Pydantic et exécute les migrations.

    On utilise `create_async_engine` directement plutôt que
    `async_engine_from_config` (qui passerait par le ConfigParser).
    """
    connectable: AsyncEngine = create_async_engine(
        DATABASE_URL,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
