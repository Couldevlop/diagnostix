# Nexus-Diagnostix

> Outil d'auto-diagnostic de maturité digitale RH pour les entreprises ivoiriennes.  
> Édité par **OpenLab Consulting** — solution **NexusRH CI**.

[![CI](https://github.com/openlab/nexus-diagnostix/actions/workflows/ci.yml/badge.svg)](./.github/workflows/ci.yml)
![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)
![Python](https://img.shields.io/badge/python-3.11-blue)
![React](https://img.shields.io/badge/react-18.3-61dafb)
![License](https://img.shields.io/badge/license-Proprietary-red)

---

## Sommaire

1. [Objectif](#1--objectif)
2. [Architecture](#2--architecture)
3. [Prérequis](#3--prérequis)
4. [Installation et démarrage](#4--installation-et-démarrage)
5. [Accès et connexions](#5--accès-et-connexions)
6. [Variables d'environnement](#6--variables-denvironnement)
7. [Gestion de la base de données](#7--gestion-de-la-base-de-données)
8. [Opérations courantes](#8--opérations-courantes)
9. [Tests](#9--tests)
10. [Structure du projet](#10--structure-du-projet)
11. [API REST](#11--api-rest)
12. [Stack technique](#12--stack-technique)
13. [Conformité & sécurité](#13--conformité--sécurité)
14. [Contact](#14--contact)

---

## 1 · Objectif

Nexus-Diagnostix évalue en **5 minutes** la maturité fiscale, sociale, de conformité et digitale d'une entreprise opérant en Côte d'Ivoire et produit un **rapport PDF premium** contenant :

- Score global sur 100 et niveau de maturité (`CRITIQUE` → `IA-NATIVE`)
- Identification chiffrée des risques de redressement CNPS & DGI (en FCFA)
- Gap digital comparé au standard IA-Native d'OpenLab
- 3 recommandations stratégiques priorisées par l'IA Claude (Anthropic)
- Prédiction du turnover et de la non-conformité à 12 mois (modèles ML scikit-learn)

---

## 2 · Architecture

```
Navigateur (React 18 + Vite + TypeScript + Tailwind)
        │ HTTPS
        ▼
API FastAPI /api/v1  ──►  PostgreSQL 16
        │               ──►  Redis 7 (cache / rate-limit)
        ▼
Claude API (Anthropic)   ──►  Anthropic claude-opus-4-7
ML local (scikit-learn)  ──►  artefacts .joblib
WeasyPrint               ──►  PDF A4 10-12 pages
```

**Pipeline de génération du rapport (4 étages) :**

```
Réponses → [1] Scoring déterministe
         → [2] Risk Engine (exposition FCFA)
         → [3] ML (non-conformité / turnover)
         → [4] Claude AI (narration + recommandations)
         → PDF WeasyPrint
```

---

## 3 · Prérequis

| Outil | Version minimale |
|---|---|
| Docker | 24+ |
| Docker Compose | v2 (plugin) ou `docker-compose` v1.29+ |
| Node.js | 20+ (dev frontend hors Docker uniquement) |
| Python | 3.11 (dev backend hors Docker uniquement) |
| Clé API Anthropic | Claude Opus 4.7 activé |

---

## 4 · Installation et démarrage

### 4.1 Cloner et configurer

```bash
git clone https://github.com/openlab/nexus-diagnostix.git
cd nexus-diagnostix

# Copier et éditer le fichier d'environnement
cp .env.example .env
# → renseigner au minimum ANTHROPIC_API_KEY et PDF_SIGNING_SECRET
```

### 4.2 Démarrer les conteneurs

```bash
# Avec le plugin Docker Compose (recommandé)
docker compose up -d

# Ou avec docker-compose standalone
docker-compose up -d
```

### 4.3 Initialiser la base de données

```bash
# Appliquer toutes les migrations Alembic
docker-compose exec backend alembic upgrade head

# Insérer les données initiales (20 questions + settings fiscaux + compte admin)
docker-compose exec backend python -m app.scripts.seed_initial_data
```

> **Note :** le backend applique `alembic upgrade head` automatiquement au démarrage via Docker.
> Le seed doit être lancé **manuellement** une seule fois.

### 4.4 Vérifier que tout tourne

```bash
docker-compose ps
# Tous les services doivent être en état "healthy" ou "Up"

curl http://localhost:8000/healthz
# {"status":"ok","database":"ok","redis":"ok"}
```

---

## 5 · Accès et connexions

### 5.1 URLs des services

| Service | URL | Description |
|---|---|---|
| **Application** | http://localhost:5173 | Interface utilisateur (React) |
| **API** | http://localhost:8000 | Backend FastAPI |
| **Swagger UI** | http://localhost:8000/api/v1/docs | Documentation interactive de l'API |
| **ReDoc** | http://localhost:8000/api/v1/redoc | Documentation alternative |
| **PostgreSQL** | localhost:**5432** | Base de données principale |
| **Redis** | localhost:**6379** | Cache et rate limiting |

### 5.2 Compte administrateur

> Connexion via http://localhost:5173/admin/login

| Champ | Valeur |
|---|---|
| **Email** | `admin@openlabconsulting.com` |
| **Mot de passe** | `Admin1234!` |
| **Rôle** | `SUPERADMIN` |

> **Sécurité :** changez ce mot de passe en production via la commande de réinitialisation (§8.3).

### 5.3 Base de données PostgreSQL

| Paramètre | Valeur (dev) |
|---|---|
| **Host** | `localhost` (depuis l'hôte) / `postgres` (inter-conteneurs) |
| **Port** | `5432` |
| **Utilisateur** | `nexus` |
| **Mot de passe** | `Admin1234!` |
| **Base** | `nexus_diagnostix` |
| **URL complète** | `postgresql://nexus:Admin1234!@localhost:5432/nexus_diagnostix` |

Connexion depuis un client SQL (DBeaver, TablePlus, psql) :
```bash
psql -h localhost -p 5432 -U nexus -d nexus_diagnostix
# Mot de passe : Admin1234!
```

Ou depuis un conteneur :
```bash
docker-compose exec postgres psql -U nexus -d nexus_diagnostix
```

### 5.4 Redis

| Paramètre | Valeur |
|---|---|
| **Host** | `localhost` (hôte) / `redis` (inter-conteneurs) |
| **Port** | `6379` |
| **Auth** | Aucune (dev) |

```bash
docker-compose exec redis redis-cli ping
# PONG
```

### 5.5 Email SMTP (Gmail)

| Paramètre | Valeur |
|---|---|
| **Hôte** | `smtp.gmail.com` |
| **Port** | `587` (STARTTLS) |
| **Utilisateur** | `coulwao@gmail.com` |
| **Expéditeur** | `NexusRH <coulwao@gmail.com>` |
| **Authentification** | App Password Gmail (16 caractères) |

> Le mot de passe SMTP est un **App Password Google** (pas le mot de passe du compte).
> Générer via : Google Account → Sécurité → Mots de passe des applications.

---

## 6 · Variables d'environnement

Toutes les variables sont dans `.env` (non versionné). Référence complète :

```dotenv
# ── Environnement ─────────────────────────────────────────────
ENVIRONMENT=development          # development | staging | production
DEBUG=true
LOG_LEVEL=INFO

# ── API ───────────────────────────────────────────────────────
API_HOST=0.0.0.0
API_PORT=8000
ALLOWED_ORIGINS=http://localhost:5173,https://diagnostix.nexusrh.ci

# ── Sécurité ──────────────────────────────────────────────────
JWT_SECRET=<chaine-aléatoire-256-bits>
JWT_ALGORITHM=HS256
BCRYPT_ROUNDS=12
FERNET_KEY=<clé-Fernet-base64>  # générer : python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
PDF_SIGNING_SECRET=<32-chars-min>
PDF_URL_TTL_DAYS=7
PASSWORD_MIN_LENGTH=12

# ── Base de données ───────────────────────────────────────────
POSTGRES_USER=nexus
POSTGRES_PASSWORD=Admin1234!
POSTGRES_DB=nexus_diagnostix
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
DATABASE_URL=postgresql+asyncpg://nexus:Admin1234!@postgres:5432/nexus_diagnostix

# ── Redis ─────────────────────────────────────────────────────
REDIS_URL=redis://redis:6379/0

# ── Claude API (Anthropic) ────────────────────────────────────
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL_EXPERT=claude-opus-4-7
CLAUDE_MODEL_CHAT=claude-sonnet-4-6
CLAUDE_TEMPERATURE=0.3
CLAUDE_TIMEOUT_SECONDS=30

# ── Email SMTP ────────────────────────────────────────────────
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587                    # 587=STARTTLS, 465=SSL
SMTP_USER=coulwao@gmail.com
SMTP_PASS=<app-password-gmail>
SMTP_FROM=NexusRH <coulwao@gmail.com>

# ── Stockage PDF ──────────────────────────────────────────────
REPORTS_STORAGE_PATH=/var/data/reports
REPORTS_RETENTION_DAYS=730

# ── Rate limiting ─────────────────────────────────────────────
RATELIMIT_PUBLIC_PER_MINUTE=60
RATELIMIT_LOGIN_PER_MINUTE=10
RATELIMIT_ADMIN_PER_MINUTE=600

# ── Admin initial ─────────────────────────────────────────────
INITIAL_ADMIN_EMAIL=admin@openlabconsulting.com
INITIAL_ADMIN_PASSWORD=Admin1234!

# ── ML ────────────────────────────────────────────────────────
ML_MODELS_PATH=/app/ml_artifacts
ML_MIN_CONFIDENCE=0.60
```

---

## 7 · Gestion de la base de données

### 7.1 Migrations Alembic

```bash
# Voir l'état actuel des migrations
docker-compose exec backend alembic current

# Appliquer toutes les migrations en attente
docker-compose exec backend alembic upgrade head

# Revenir en arrière d'une migration
docker-compose exec backend alembic downgrade -1

# Créer une nouvelle migration (après modification d'un modèle SQLAlchemy)
docker-compose exec backend alembic revision --autogenerate -m "description_courte"
```

### 7.2 Migrations disponibles

| Révision | Description |
|---|---|
| `0001` | Création du schéma initial (questions, sessions, responses, reports, users, audit_logs, settings) |
| `0002` | Ajout colonne `status` sur la table `reports` |

### 7.3 Seed des données initiales

```bash
docker-compose exec backend python -m app.scripts.seed_initial_data
```

Ce script insère (idempotent — sûr à ré-exécuter) :
- Les **20 questions** du diagnostic avec leurs pondérations
- Les **paramètres fiscaux CI 2026** (CNPS, IGR, SMIG, IFC, FDFP)
- Le **compte SUPERADMIN** initial

---

## 8 · Opérations courantes

### 8.1 Logs des conteneurs

```bash
# Tous les services
docker-compose logs -f

# Backend uniquement (JSON structuré)
docker-compose logs -f backend

# Frontend (Vite HMR)
docker-compose logs -f frontend
```

### 8.2 Redémarrer un service

```bash
docker-compose restart backend
docker-compose restart frontend
```

### 8.3 Réinitialiser le mot de passe admin

Si le compte admin est verrouillé (5 tentatives échouées) ou si le mot de passe est oublié :

1. Mettre à jour `INITIAL_ADMIN_PASSWORD` dans `.env`
2. Lancer le script :

```bash
docker-compose exec backend python -m app.scripts.reset_admin_password
```

Ce script remet le hash du mot de passe, déverrouille le compte (`failed_attempts=0`, `locked_until=NULL`) et réactive l'utilisateur.

### 8.4 Accéder au shell du backend

```bash
docker-compose exec backend bash
# ou Python interactif :
docker-compose exec backend python
```

### 8.5 Purger et recréer la base

```bash
# ⚠️ DÉTRUIT toutes les données
docker-compose down -v
docker-compose up -d
docker-compose exec backend alembic upgrade head
docker-compose exec backend python -m app.scripts.seed_initial_data
```

### 8.6 Entraîner / recharger les modèles ML

```bash
# Générer le dataset synthétique d'entraînement
docker-compose exec backend python -m app.scripts.generate_training_data

# Entraîner et exporter les modèles .joblib
docker-compose exec backend python -m app.scripts.train_models
```

Les artefacts sont stockés dans le volume `ml_artifacts` (`/app/ml_artifacts`).

---

## 9 · Tests

### 9.1 Backend (pytest)

```bash
# Tous les tests avec couverture
docker-compose exec backend pytest --cov=app --cov-report=term-missing

# Couverture exigée à 100 % sur les modules métier
docker-compose exec backend pytest --cov=app --cov-fail-under=100

# Un seul fichier
docker-compose exec backend pytest tests/unit/test_scoring_engine.py -v

# Tests d'intégration uniquement
docker-compose exec backend pytest tests/integration/ -v
```

**Fichiers de tests :**

| Fichier | Type | Description |
|---|---|---|
| `tests/unit/test_scoring_engine.py` | Unitaire | Moteur de scoring (5 snapshots) |
| `tests/unit/test_risk_engine.py` | Unitaire | Moteur de risque & exposition FCFA |
| `tests/unit/test_ml_engine.py` | Unitaire | Prédictions ML (mock modèles) |
| `tests/unit/test_ci_fiscal.py` | Unitaire | Barèmes IGR, CNPS, IFC, heures sup. |
| `tests/unit/test_ai_service.py` | Unitaire | Wrapper Claude API (mock Anthropic) |
| `tests/unit/test_email_service.py` | Unitaire | Envoi email (mock SMTP) |
| `tests/unit/test_report_service.py` | Unitaire | Génération PDF WeasyPrint |
| `tests/unit/test_security.py` | Unitaire | Hash, JWT, vérifications |
| `tests/unit/test_app.py` | Unitaire | App FastAPI, routes, middleware |
| `tests/integration/test_questionnaire_api.py` | Intégration | Sessions, questions, finalize |
| `tests/integration/test_auth_admin_api.py` | Intégration | Auth JWT, endpoints admin |

### 9.2 Frontend (Vitest)

```bash
docker-compose exec frontend npm run test
# ou hors Docker :
cd frontend && npm run test
```

### 9.3 E2E (Playwright)

```bash
cd frontend && npx playwright test
# Rapport HTML :
npx playwright show-report
```

---

## 10 · Structure du projet

```
nexus-diagnostix/
├── CLAUDE.md                    ← Spécification d'ingénierie (source de vérité)
├── README.md                    ← Ce fichier
├── docker-compose.yml           ← Dev local (hot-reload)
├── docker-compose.prod.yml      ← Production (multi-stage builds)
├── .env                         ← Variables (non versionné)
├── .env.example                 ← Template
├── .github/workflows/
│   └── ci.yml                   ← Pipeline CI GitHub Actions
│
├── backend/
│   ├── pyproject.toml           ← Dépendances Python + config ruff/mypy/pytest
│   ├── Dockerfile
│   ├── alembic.ini
│   ├── alembic/versions/        ← Migrations SQL versionnées
│   └── app/
│       ├── main.py              ← Entrée FastAPI
│       ├── config.py            ← Settings Pydantic (depuis .env)
│       ├── database.py          ← Session async SQLAlchemy
│       ├── api/v1/              ← Routeurs REST
│       │   ├── questionnaire.py ← POST /sessions, GET questions, POST finalize
│       │   ├── responses.py     ← POST /sessions/{id}/responses
│       │   ├── reports.py       ← GET /reports/{id}, GET pdf, POST send
│       │   ├── admin.py         ← CRUD questions/settings, stats, leads, audit
│       │   └── auth.py          ← POST /auth/login, POST /auth/refresh
│       ├── models/              ← SQLAlchemy ORM
│       ├── schemas/             ← Pydantic v2 (validation I/O)
│       ├── services/
│       │   ├── scoring_engine.py   ← Score global + sous-scores par catégorie
│       │   ├── risk_engine.py      ← Exposition financière FCFA
│       │   ├── ml_engine.py        ← Prédiction non-conformité / turnover
│       │   ├── ai_service.py       ← Wrapper Claude API + cache Redis + fallback
│       │   ├── report_service.py   ← Génération PDF WeasyPrint + URL signée
│       │   └── email_service.py    ← SMTP (aiosmtplib) ou SendGrid
│       ├── core/
│       │   ├── ci_fiscal.py        ← Barèmes IGR 2024, CNPS, IFC, FDFP
│       │   ├── security.py         ← bcrypt, JWT, HMAC
│       │   └── exceptions.py       ← NotFoundError, ConflictError, ValidationError
│       ├── scripts/
│       │   ├── seed_initial_data.py
│       │   └── reset_admin_password.py
│       └── templates/
│           └── report.html         ← Template Jinja2 du rapport PDF
│
└── frontend/
    ├── package.json
    ├── vite.config.ts
    ├── tailwind.config.ts
    ├── Dockerfile
    └── src/
        ├── pages/
        │   ├── Landing.tsx          ← Page d'accueil
        │   ├── DiagnosticStart.tsx  ← Formulaire pré-diagnostic
        │   ├── Questionnaire.tsx    ← 1 question / écran
        │   ├── Generating.tsx       ← Loader + polling
        │   ├── ReportView.tsx       ← Rapport interactif
        │   ├── AdminLogin.tsx       ← Connexion admin
        │   ├── AdminDashboard.tsx   ← Dashboard admin (5 onglets)
        │   └── NotFound.tsx         ← 404
        ├── lib/
        │   ├── api.ts               ← Client HTTP typé + gestion d'erreurs
        │   └── auth.ts              ← JWT localStorage
        └── styles/
            └── globals.css          ← Palette OpenLab + composants Tailwind
```

---

## 11 · API REST

Préfixe : `/api/v1` · Format : JSON UTF-8 · Erreurs : RFC 7807

### Endpoints publics

| Méthode | Route | Description |
|---|---|---|
| `POST` | `/sessions` | Démarrer une session de diagnostic |
| `GET` | `/sessions/{id}/questions` | Liste ordonnée des 20 questions |
| `POST` | `/sessions/{id}/responses` | Enregistrer une réponse (idempotent) |
| `POST` | `/sessions/{id}/finalize` | Verrouiller + déclencher la génération |
| `GET` | `/reports/{id}` | Polling du rapport (status: GENERATING → READY) |
| `GET` | `/reports/{id}/pdf` | Stream PDF (token HMAC signé, TTL 7j) |
| `POST` | `/reports/{id}/send` | Envoyer le rapport par email |
| `GET` | `/healthz` | Liveness probe |
| `GET` | `/readyz` | Readiness probe (BDD + Redis + API) |

### Endpoints admin (JWT obligatoire)

| Méthode | Route | Description |
|---|---|---|
| `POST` | `/auth/login` | Login → JWT (TTL 8h) |
| `POST` | `/auth/refresh` | Renouveler le token |
| `GET` | `/admin/questions` | Liste paginée des questions |
| `PUT` | `/admin/questions/{id}` | Modifier libellé / poids / aide |
| `PATCH` | `/admin/questions/{id}/toggle` | Activer / désactiver |
| `GET` | `/admin/settings` | Paramètres fiscaux & sociaux |
| `PUT` | `/admin/settings/{key}` | Modifier un paramètre |
| `GET` | `/admin/stats` | KPIs agrégés |
| `GET` | `/admin/leads` | Emails opt-in (JSON ou CSV) |
| `GET` | `/admin/audit-logs` | Journal d'audit filtrable |

### Exemple de session complète

```bash
# 1. Créer la session
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{"company_size":"51-200","sector":"Services & Conseil","contact_consent":false}'
# → {"session_id":"uuid...","total_questions":20}

# 2. Enregistrer une réponse
curl -X POST http://localhost:8000/api/v1/sessions/{uuid}/responses \
  -H "Content-Type: application/json" \
  -d '{"question_id":1,"answer_value":"YES"}'

# 3. Finaliser (après les 20 réponses)
curl -X POST http://localhost:8000/api/v1/sessions/{uuid}/finalize

# 4. Récupérer le rapport (polling)
curl http://localhost:8000/api/v1/reports/{report_id}
```

---

## 12 · Stack technique

### Backend

| Composant | Version | Rôle |
|---|---|---|
| Python | 3.11 | Runtime |
| FastAPI | 0.115+ | API async, OpenAPI auto |
| Pydantic | 2.x | Validation stricte |
| SQLAlchemy | 2.x async | ORM |
| Alembic | 1.13+ | Migrations |
| asyncpg | 0.29+ | Driver PostgreSQL async |
| anthropic | 0.40+ | SDK Claude AI |
| WeasyPrint | 62+ | Génération PDF |
| scikit-learn | 1.5+ | Modèles ML |
| aiosmtplib | latest | SMTP async |
| structlog | latest | Logs JSON structurés |
| ruff | 0.6+ | Linter + formateur |
| pytest | 8+ | Tests |

### Frontend

| Composant | Version | Rôle |
|---|---|---|
| React | 18.3 | UI |
| TypeScript | 5.5 | Typage |
| Vite | 5.4 | Bundler |
| TailwindCSS | 3.4 | Styles |
| Framer Motion | 11+ | Animations |
| Lucide React | latest | Icônes |
| Vitest | 2+ | Tests unitaires |

### Infrastructure (dev)

| Service | Image Docker | Port |
|---|---|---|
| PostgreSQL | `postgres:16-alpine` | 5432 |
| Redis | `redis:7-alpine` | 6379 |
| Backend FastAPI | `./backend` (Dockerfile) | 8000 |
| Frontend Vite | `./frontend` (Dockerfile) | 5173 |

---

## 13 · Conformité & sécurité

- **ARTCI Loi 2013-450** : aucune donnée nominative obligatoire, email chiffré (Fernet AES-256) si opt-in, droit d'effacement via `dpo@openlabconsulting.com`
- **Rate limiting** : 60 req/min (public), 10 req/min (login), 600 req/min (admin)
- **JWT** : HS256, TTL 8h, rotation du secret recommandée trimestriellement
- **Mots de passe** : bcrypt cost 12, minimum 12 caractères
- **Verrouillage** : compte admin bloqué après 5 tentatives échouées
- **PDF** : URL signée HMAC-SHA256, TTL 7 jours
- **Headers HTTP** : HSTS, X-Frame-Options: DENY, X-Content-Type-Options: nosniff, CSP strict

---

## 14 · Contact

| | |
|---|---|
| **Éditeur** | OpenLab Consulting |
| **Produit** | NexusRH CI |
| **Site** | https://www.openlabconsulting.com |
| **DPO** | dpo@openlabconsulting.com |
| **Support** | cti.intelligency@gmail.com |
| **Téléphone** | +225 07 09 33 42 38 |
| **Adresse** | Abidjan, Côte d'Ivoire |

---

© 2026 OpenLab Consulting — Tous droits réservés.  
Spécification complète : [CLAUDE.md](./CLAUDE.md)
