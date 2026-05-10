# Backend — Nexus-Diagnostix

API FastAPI + PostgreSQL + Redis + Claude API + scikit-learn.

## Démarrage local (sans Docker)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Variables d'environnement
cp ../.env.example ../.env  # à éditer

# Migrations
alembic upgrade head

# Données initiales
python -m app.scripts.seed_initial_data

# Serveur
uvicorn app.main:app --reload
```

## Tests

```bash
# Tous les tests + couverture
pytest --cov=app --cov-report=term-missing

# Couverture 100 % imposée (CI)
pytest --cov=app --cov-fail-under=100

# Mutation testing sur les modules critiques
mutmut run --paths-to-mutate app/core/ci_fiscal.py,app/services/scoring_engine.py
```

## Qualité

```bash
ruff check app tests        # lint
ruff format app tests       # format
mypy app                    # type check strict
pip-audit                   # CVE
```

## Structure

```
app/
├── api/v1/         # endpoints REST
├── core/           # transverse : ci_fiscal, security, prompts
├── models/         # SQLAlchemy ORM
├── schemas/        # Pydantic (request/response)
├── services/       # logique métier
├── templates/      # templates Jinja2 (PDF)
├── scripts/        # seed, training ML
├── config.py       # Settings Pydantic
├── database.py     # session async
└── main.py         # entry point FastAPI
```

Voir [`../CLAUDE.md`](../CLAUDE.md) pour la spec complète.
