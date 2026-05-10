# Nexus-Diagnostix

> Outil d'auto-diagnostic de maturité digitale RH pour les entreprises ivoiriennes.
> Édité par **OpenLab Consulting** — solution **NexusRH CI**.

[![CI](https://github.com/openlab/nexus-diagnostix/actions/workflows/ci.yml/badge.svg)](./.github/workflows/ci.yml)
![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)
![License](https://img.shields.io/badge/license-Proprietary-red)

---

## 🎯 Objet

Évalue en 5 minutes la maturité fiscale, sociale, de conformité et digitale d'une entreprise opérant en Côte d'Ivoire, et produit un **rapport PDF premium** avec :

- Score global sur 100 et niveau de maturité (`CRITIQUE` → `IA-NATIVE`).
- Identification chiffrée des risques de redressement CNPS et fiscaux (en FCFA).
- Gap digital comparé au standard IA-Native d'OpenLab.
- 3 recommandations stratégiques priorisées par l'IA Claude.
- Prédiction du turnover et de la non-conformité à 12 mois (modèles ML).

---

## 🚀 Démarrage rapide

### Prérequis

- Docker 24+ et Docker Compose v2
- Node.js 20+ (dev frontend hors Docker)
- Python 3.11 (dev backend hors Docker)
- Une clé API Anthropic (Claude)

### Lancement complet

```bash
git clone https://github.com/openlab/nexus-diagnostix.git
cd nexus-diagnostix
cp .env.example .env
# éditer .env et renseigner ANTHROPIC_API_KEY
docker compose up -d
```

Services accessibles :

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| API | http://localhost:8000 |
| OpenAPI (Swagger) | http://localhost:8000/api/v1/docs |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

### Initialiser la base

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.scripts.seed_initial_data
```

Compte admin créé : `admin@openlabconsulting.com` / mot de passe affiché en console au premier démarrage.

---

## 📚 Documentation

- **[CLAUDE.md](./CLAUDE.md)** — spécification d'ingénierie complète (source unique de vérité).
- [docs/architecture.md](./docs/architecture.md) — schémas et choix techniques.
- [docs/api.md](./docs/api.md) — contrat REST détaillé.
- [docs/ml-methodology.md](./docs/ml-methodology.md) — méthodologie ML et dataset.
- [docs/security.md](./docs/security.md) — modèle de menaces et mesures.

---

## 🧪 Tests

```bash
# Backend — couverture 100 % exigée
docker compose exec backend pytest --cov=app --cov-fail-under=100

# Frontend
docker compose exec frontend npm run test

# E2E
docker compose exec frontend npx playwright test
```

---

## 🗂️ Structure

Voir [CLAUDE.md §4](./CLAUDE.md) pour le détail de chaque répertoire.

```
nexus-diagnostix/
├── backend/        # FastAPI + SQLAlchemy + ML + Claude API
├── frontend/       # React 18 + Vite + TS + Tailwind + shadcn/ui
├── docs/           # Documentation technique
├── .github/        # CI/CD GitHub Actions
└── docker-compose.yml
```

---

## 📜 Licence

Propriétaire — © 2026 OpenLab Consulting. Tous droits réservés.

## 📞 Contact

- Site : https://www.openlabconsulting.com
- DPO : dpo@openlabconsulting.com
- Tél : +225 07 09 33 42 38
