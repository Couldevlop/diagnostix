# CLAUDE.md — Nexus-Diagnostix

> **Spécification d'ingénierie pour Claude Code (Anthropic).**
> Ce document est la **source unique de vérité** pour la conception, le développement, les tests et le déploiement de l'application **Nexus-Diagnostix**, l'outil d'auto-diagnostic de maturité digitale RH d'OpenLab Consulting / NexusRH CI.
>
> **Règle d'or :** aucun code généré ne doit contenir de `TODO`, de `pass`, de `// ...`, de mock non documenté, ni de fonction stub. Tout module livré doit être **exécutable, testé, et couvert à 100 %** avant de passer au suivant.

---

## Sommaire

1. [Mission et périmètre](#1-mission-et-périmètre)
2. [Architecture cible](#2-architecture-cible)
3. [Stack technique imposée](#3-stack-technique-imposée)
4. [Structure du dépôt](#4-structure-du-dépôt)
5. [Modèle de données](#5-modèle-de-données)
6. [API REST — contrat complet](#6-api-rest--contrat-complet)
7. [Moteur de calcul fiscal et social CI](#7-moteur-de-calcul-fiscal-et-social-ci)
8. [Moteur IA — Analyse, prédiction, recommandations](#8-moteur-ia--analyse-prédiction-recommandations)
9. [Frontend — UX, UI, parcours](#9-frontend--ux-ui-parcours)
10. [Génération du rapport PDF](#10-génération-du-rapport-pdf)
11. [Sécurité et conformité ARTCI](#11-sécurité-et-conformité-artci)
12. [Stratégie de tests — couverture 100 %](#12-stratégie-de-tests--couverture-100-)
13. [DevOps, CI/CD, hébergement](#13-devops-cicd-hébergement)
14. [Plan d'exécution séquentiel pour Claude Code](#14-plan-dexécution-séquentiel-pour-claude-code)
15. [Critères d'acceptation finaux](#15-critères-dacceptation-finaux)

---

## 1. Mission et périmètre

### 1.1 Objectif produit

Nexus-Diagnostix est un **SaaS d'auto-diagnostic de maturité digitale RH** destiné aux DRH, responsables paie, dirigeants et consultants opérant en Côte d'Ivoire. À partir d'un questionnaire de 20 questions pondérées, l'application :

- calcule un **score global sur 100** ;
- identifie les **risques de redressement CNPS et fiscaux** ;
- mesure le **gap digital** par rapport au standard "IA-Native" d'OpenLab ;
- prédit la **probabilité de non-conformité** à 12 mois ;
- estime l'**exposition financière** (en FCFA) en cas de contrôle ;
- génère un **rapport PDF premium** transmissible par email ou lien sécurisé.

### 1.2 Comptes et rôles

| Rôle | Permissions |
|---|---|
| **Visiteur (anonyme)** | Remplit le questionnaire, reçoit son rapport par email. Aucune donnée nominative stockée (conformité ARTCI Loi 2013-450). |
| **Utilisateur authentifié** | Conserve l'historique de ses diagnostics, peut comparer ses scores dans le temps. |
| **Admin** | Gère les questions, pondérations, taux fiscaux/sociaux, consulte les statistiques agrégées anonymisées, exporte les leads opt-in. |

### 1.3 Hors périmètre (V1)

- Pas d'intégration directe avec les SI clients (CNPS, DGI).
- Pas de paiement en ligne — l'outil est gratuit.
- Pas d'application mobile native (responsive web suffisant).

---

## 2. Architecture cible

```
┌──────────────────────────────────────────────────────────────┐
│                     CLIENT (navigateur)                      │
│                                                              │
│   React 18 + Vite + TypeScript + TailwindCSS + shadcn/ui     │
│   ─ Landing page                                             │
│   ─ Questionnaire dynamique (1 question / écran)             │
│   ─ Espace admin (auth JWT)                                  │
│   ─ Visualisation rapport (PDF embarqué)                     │
└────────────────────────────┬─────────────────────────────────┘
                             │ HTTPS / TLS 1.3
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                   API (FastAPI / Python 3.11)                │
│                                                              │
│   ─ Routeur /api/v1                                          │
│   ─ Service Questionnaire                                    │
│   ─ Service Scoring (moteur déterministe)                    │
│   ─ Service IA (Claude API + ML local)                       │
│   ─ Service Rapport (WeasyPrint)                             │
│   ─ Service Email (SMTP / SendGrid)                          │
│   ─ Service Auth (OAuth2 + JWT)                              │
└──────────┬──────────────────────────┬────────────────────────┘
           │                          │
           ▼                          ▼
┌────────────────────┐   ┌────────────────────────────────────┐
│   PostgreSQL 16    │   │   Anthropic Claude API             │
│   ─ AES-256 at rest│   │   ─ claude-opus-4-7 (analyse)      │
│   ─ Backups H+1    │   │   ─ claude-sonnet-4-6 (chat admin) │
└────────────────────┘   └────────────────────────────────────┘
           │
           ▼
┌────────────────────┐
│   Redis 7          │
│   ─ Rate limiting  │
│   ─ Cache scores   │
│   ─ Job queue (RQ) │
└────────────────────┘
```

### 2.1 Principes architecturaux

- **Séparation stricte** front / back (CORS contrôlé, pas de SSR).
- **Stateless API** : tout l'état métier en BDD, sessions via JWT.
- **Idempotence** des endpoints d'écriture (header `Idempotency-Key`).
- **12-Factor App** : config par variables d'environnement, logs sur stdout.
- **Versionnage API** : préfixe `/api/v1` obligatoire.

---

## 3. Stack technique imposée

### 3.1 Backend

| Composant | Version | Justification |
|---|---|---|
| Python | 3.11.x | LTS, performances, typage moderne |
| FastAPI | 0.115+ | Async natif, OpenAPI auto, validation Pydantic |
| Pydantic | 2.x | Validation stricte des schémas |
| SQLAlchemy | 2.x (async) | ORM mature, async/await |
| Alembic | 1.13+ | Migrations versionnées |
| asyncpg | 0.29+ | Driver PostgreSQL async |
| anthropic | 0.40+ | SDK officiel Claude |
| WeasyPrint | 62+ | HTML→PDF haute qualité, supporte CSS print |
| scikit-learn | 1.5+ | Modèles ML (Random Forest, Logistic Regression) |
| numpy / pandas | latest | Calcul vectoriel |
| pytest | 8+ | Framework de tests |
| pytest-asyncio | 0.23+ | Tests async |
| pytest-cov | 5+ | Couverture |
| httpx | 0.27+ | Client HTTP de test |
| ruff | 0.6+ | Linter + formatter |
| mypy | 1.11+ | Vérification typage stricte |

### 3.2 Frontend

| Composant | Version |
|---|---|
| React | 18.3 |
| TypeScript | 5.5 |
| Vite | 5.4 |
| TailwindCSS | 3.4 |
| shadcn/ui | latest |
| Framer Motion | 11+ |
| TanStack Query | 5+ |
| React Hook Form + Zod | 7+ / 3+ |
| Recharts | 2.12 |
| Vitest + Testing Library | 2+ / 16+ |
| Playwright | 1.47+ (E2E) |

### 3.3 Infra

- **Docker** + **docker-compose** pour le dev local.
- **PostgreSQL 16** (alpine), volume persistant chiffré.
- **Redis 7** (alpine).
- **Nginx** comme reverse proxy / TLS termination.
- **GitHub Actions** pour CI/CD.
- **OVH Public Cloud (Gravelines)** ou **AWS eu-west-3 (Paris)** — proximité géographique CI.

---

## 4. Structure du dépôt

```
nexus-diagnostix/
├── CLAUDE.md                        ← ce fichier
├── README.md
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── .github/
│   └── workflows/
│       ├── ci.yml                   ← lint + tests + couverture
│       └── deploy.yml
│
├── backend/
│   ├── pyproject.toml
│   ├── Dockerfile
│   ├── alembic.ini
│   ├── alembic/
│   │   └── versions/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  ← entry point FastAPI
│   │   ├── config.py                ← Pydantic Settings
│   │   ├── database.py              ← session async SQLAlchemy
│   │   ├── dependencies.py
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── router.py
│   │   │       ├── questionnaire.py
│   │   │       ├── responses.py
│   │   │       ├── reports.py
│   │   │       ├── admin.py
│   │   │       └── auth.py
│   │   ├── models/
│   │   │   ├── question.py
│   │   │   ├── response.py
│   │   │   ├── report.py
│   │   │   ├── user.py
│   │   │   └── audit_log.py
│   │   ├── schemas/                 ← Pydantic
│   │   │   ├── question.py
│   │   │   ├── response.py
│   │   │   └── report.py
│   │   ├── services/
│   │   │   ├── scoring_engine.py    ← moteur déterministe
│   │   │   ├── risk_engine.py       ← calcul exposition FCFA
│   │   │   ├── ml_engine.py         ← prédiction turnover/non-conformité
│   │   │   ├── ai_service.py        ← wrapper Claude API
│   │   │   ├── report_service.py    ← génération PDF
│   │   │   └── email_service.py
│   │   ├── core/
│   │   │   ├── security.py          ← hash, JWT
│   │   │   ├── ci_fiscal.py         ← barème IGR 2024, CNPS, IFC
│   │   │   └── exceptions.py
│   │   └── templates/
│   │       └── report.html          ← template Jinja2 du rapport PDF
│   └── tests/
│       ├── conftest.py
│       ├── unit/
│       │   ├── test_scoring_engine.py
│       │   ├── test_risk_engine.py
│       │   ├── test_ml_engine.py
│       │   ├── test_ci_fiscal.py
│       │   └── test_report_service.py
│       ├── integration/
│       │   ├── test_questionnaire_api.py
│       │   ├── test_responses_api.py
│       │   └── test_reports_api.py
│       └── fixtures/
│           ├── questions.json
│           └── responses_samples.json
│
└── frontend/
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    ├── tailwind.config.ts
    ├── Dockerfile
    ├── public/
    ├── src/
    │   ├── main.tsx
    │   ├── App.tsx
    │   ├── routes.tsx
    │   ├── lib/
    │   │   ├── api.ts               ← client TanStack Query
    │   │   ├── auth.ts
    │   │   └── utils.ts
    │   ├── components/
    │   │   ├── ui/                  ← shadcn
    │   │   ├── questionnaire/
    │   │   │   ├── QuestionCard.tsx
    │   │   │   ├── ProgressBar.tsx
    │   │   │   ├── AnswerOptions.tsx
    │   │   │   └── NavigationFooter.tsx
    │   │   ├── report/
    │   │   │   ├── ScoreGauge.tsx
    │   │   │   ├── RiskMatrix.tsx
    │   │   │   ├── GapDigitalChart.tsx
    │   │   │   └── RecommendationCard.tsx
    │   │   └── admin/
    │   │       ├── QuestionEditor.tsx
    │   │       ├── StatsDashboard.tsx
    │   │       └── LeadsTable.tsx
    │   ├── pages/
    │   │   ├── Landing.tsx
    │   │   ├── Diagnostic.tsx
    │   │   ├── ReportView.tsx
    │   │   ├── AdminLogin.tsx
    │   │   └── AdminDashboard.tsx
    │   ├── hooks/
    │   │   ├── useQuestionnaire.ts
    │   │   └── useReport.ts
    │   └── styles/
    │       └── globals.css
    └── tests/
        ├── unit/
        └── e2e/
```

---

## 5. Modèle de données

### 5.1 Schéma PostgreSQL

```sql
-- Questions du diagnostic (gérées par l'admin)
CREATE TABLE questions (
    id              SERIAL PRIMARY KEY,
    code            VARCHAR(10) UNIQUE NOT NULL,        -- ex: 'Q01'
    label           TEXT NOT NULL,
    category        VARCHAR(20) NOT NULL CHECK (category IN ('FISCALE','SOCIALE','CONFORMITE','DIGITALE')),
    weight          INTEGER NOT NULL CHECK (weight BETWEEN 1 AND 20),
    answer_type     VARCHAR(20) NOT NULL CHECK (answer_type IN ('YES_NO','YES_NO_PARTIAL','YES_NO_MANUAL','FREE_NUMERIC')),
    "order"         INTEGER NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    help_text       TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Sessions de diagnostic (1 visiteur = 1 session)
CREATE TABLE diagnostic_sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_size    VARCHAR(20),                         -- '1-10','11-50','51-200','201-500','500+'
    sector          VARCHAR(50),
    contact_email   VARCHAR(255),                        -- chiffré AES-256, opt-in obligatoire
    contact_consent BOOLEAN NOT NULL DEFAULT FALSE,
    ip_hash         VARCHAR(64) NOT NULL,                -- SHA-256 de l'IP, anti-spam
    user_agent_hash VARCHAR(64),
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ,
    status          VARCHAR(20) NOT NULL DEFAULT 'IN_PROGRESS'
                    CHECK (status IN ('IN_PROGRESS','COMPLETED','ABANDONED'))
);
CREATE INDEX idx_sessions_status ON diagnostic_sessions(status);
CREATE INDEX idx_sessions_completed ON diagnostic_sessions(completed_at);

-- Réponses individuelles
CREATE TABLE responses (
    id              SERIAL PRIMARY KEY,
    session_id      UUID NOT NULL REFERENCES diagnostic_sessions(id) ON DELETE CASCADE,
    question_id     INTEGER NOT NULL REFERENCES questions(id),
    answer_value    VARCHAR(50) NOT NULL,                -- 'YES','NO','PARTIAL','MANUAL', ou numérique
    answer_numeric  NUMERIC,                             -- pour FREE_NUMERIC
    answered_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (session_id, question_id)
);

-- Rapports générés
CREATE TABLE reports (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id          UUID NOT NULL UNIQUE REFERENCES diagnostic_sessions(id) ON DELETE CASCADE,
    global_score        NUMERIC(5,2) NOT NULL CHECK (global_score BETWEEN 0 AND 100),
    score_fiscale       NUMERIC(5,2) NOT NULL,
    score_sociale       NUMERIC(5,2) NOT NULL,
    score_conformite    NUMERIC(5,2) NOT NULL,
    score_digitale      NUMERIC(5,2) NOT NULL,
    maturity_level      VARCHAR(20) NOT NULL,            -- 'CRITIQUE','EMERGENT','STRUCTURE','OPTIMISE','IA_NATIVE'
    risk_score          NUMERIC(5,2) NOT NULL,           -- 0-100, 100 = risque max
    financial_exposure  NUMERIC(15,2) NOT NULL,          -- FCFA
    turnover_risk_proba NUMERIC(4,3) NOT NULL,           -- 0.000 à 1.000
    digital_gap_pct     NUMERIC(5,2) NOT NULL,           -- % vs standard IA-Native
    ai_analysis         JSONB NOT NULL,                  -- payload structuré renvoyé par Claude
    recommendations     JSONB NOT NULL,                  -- 3 recos prioritaires
    pdf_path            VARCHAR(500),
    pdf_signed_url      TEXT,
    pdf_url_expires_at  TIMESTAMPTZ,
    generated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sent_to_email       BOOLEAN NOT NULL DEFAULT FALSE,
    sent_at             TIMESTAMPTZ
);

-- Comptes admin
CREATE TABLE users (
    id              SERIAL PRIMARY KEY,
    email           VARCHAR(255) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,               -- bcrypt cost 12
    role            VARCHAR(20) NOT NULL DEFAULT 'ADMIN' CHECK (role IN ('ADMIN','SUPERADMIN')),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    last_login_at   TIMESTAMPTZ,
    failed_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Journal d'audit (rétention 6 mois — purge automatique)
CREATE TABLE audit_logs (
    id              BIGSERIAL PRIMARY KEY,
    actor_type      VARCHAR(20) NOT NULL,                -- 'ADMIN','VISITOR','SYSTEM'
    actor_id        VARCHAR(64),
    action          VARCHAR(50) NOT NULL,
    resource_type   VARCHAR(50),
    resource_id     VARCHAR(64),
    payload         JSONB,
    ip_hash         VARCHAR(64),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_audit_created ON audit_logs(created_at);

-- Paramètres globaux (taux fiscaux, plafonds, modifiables par admin)
CREATE TABLE settings (
    key             VARCHAR(50) PRIMARY KEY,
    value           JSONB NOT NULL,
    description     TEXT,
    updated_by      INTEGER REFERENCES users(id),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 5.2 Données de seed obligatoires

Le script `alembic/seeds/initial_data.py` doit insérer :

- les **20 questions** exactement telles que listées en Annexe 2 du cahier des charges, avec les pondérations imposées ;
- les **paramètres CI 2026** dans `settings` :
  - `cnps_employer_rate` : `0.105`
  - `cnps_employee_rate` : `0.055`
  - `cnps_ceiling_monthly` : `600000`
  - `igr_brackets_2024` : barème complet (cf. §7.1)
  - `smig_monthly` : `75000`
  - `fdfp_rate` : `0.012`
- un **compte SUPERADMIN** initial : `admin@openlabconsulting.com` / mot de passe à régénérer au premier login.

---

## 6. API REST — contrat complet

> Toutes les routes sont préfixées par `/api/v1`. Les réponses sont en JSON, encodage UTF-8. Erreurs au format **RFC 7807** (Problem Details).

### 6.1 Public — questionnaire et diagnostic

#### `POST /sessions`
Démarre une session de diagnostic.

**Request body :**
```json
{
  "company_size": "51-200",
  "sector": "BTP",
  "contact_email": "drh@example.ci",
  "contact_consent": true
}
```

**Response 201 :**
```json
{
  "session_id": "8f3e...",
  "started_at": "2026-05-07T10:00:00Z",
  "total_questions": 20
}
```

#### `GET /sessions/{session_id}/questions`
Renvoie la liste ordonnée des questions actives.

**Response 200 :**
```json
{
  "questions": [
    {
      "id": 1,
      "code": "Q01",
      "label": "Vos bulletins de paie intègrent-ils la réforme IGR 2024 ?",
      "category": "FISCALE",
      "answer_type": "YES_NO_PARTIAL",
      "order": 1,
      "help_text": "La réforme IGR 2024 introduit..."
    }
  ]
}
```

#### `POST /sessions/{session_id}/responses`
Enregistre la réponse à **une seule** question (idempotent par `(session_id, question_id)`).

**Request body :**
```json
{
  "question_id": 1,
  "answer_value": "PARTIAL"
}
```

**Response 200 :**
```json
{
  "saved": true,
  "progress": { "answered": 1, "total": 20, "percent": 5.0 }
}
```

#### `POST /sessions/{session_id}/finalize`
Verrouille la session, déclenche le calcul du score, l'analyse IA et la génération du PDF.

**Response 202 :**
```json
{
  "report_id": "a1b2...",
  "status": "GENERATING",
  "estimated_seconds": 15
}
```

#### `GET /reports/{report_id}`
Renvoie le rapport JSON (polling autorisé toutes les 2 s).

**Response 200 (terminé) :**
```json
{
  "report_id": "a1b2...",
  "status": "READY",
  "global_score": 47.5,
  "maturity_level": "EMERGENT",
  "scores_by_category": { "FISCALE": 60, "SOCIALE": 40, "CONFORMITE": 50, "DIGITALE": 35 },
  "risk_score": 72.3,
  "financial_exposure_fcfa": 18500000,
  "turnover_risk_proba": 0.34,
  "digital_gap_pct": 65.0,
  "executive_summary": "...",
  "risks_detected": [ { "id": "R1", "title": "...", "severity": "HIGH", "fcfa_impact": 12000000 } ],
  "recommendations": [ { "priority": 1, "title": "...", "description": "...", "expected_gain": "..." } ],
  "pdf_url": "https://api.nexusrh.ci/api/v1/reports/a1b2.../pdf?token=...",
  "generated_at": "2026-05-07T10:05:30Z"
}
```

#### `GET /reports/{report_id}/pdf`
Stream du PDF (header `Content-Type: application/pdf`). Auth par token signé (HMAC-SHA256, TTL 7 jours).

#### `POST /reports/{report_id}/send`
Envoie le rapport par email à l'adresse de la session (si `contact_consent=true`).

### 6.2 Admin

Toutes ces routes exigent `Authorization: Bearer <JWT>`.

| Méthode | Route | Description |
|---|---|---|
| `POST` | `/auth/login` | Login admin (email + mot de passe → JWT 8 h) |
| `POST` | `/auth/refresh` | Refresh token |
| `GET` | `/admin/questions` | Liste paginée |
| `PUT` | `/admin/questions/{id}` | Modifier libellé / poids / ordre |
| `PATCH` | `/admin/questions/{id}/toggle` | Activer / désactiver |
| `GET` | `/admin/settings` | Récupère tous les paramètres |
| `PUT` | `/admin/settings/{key}` | Modifie un paramètre |
| `GET` | `/admin/stats` | KPIs agrégés (nb sessions, score moyen, taux complétion, distribution maturité) |
| `GET` | `/admin/leads` | Liste des emails opt-in (CSV ou JSON) |
| `GET` | `/admin/audit-logs` | Journal filtrable |

### 6.3 Conventions transverses

- **Rate limiting** : 60 req/min/IP en public, 600 req/min pour admin.
- **CORS** : whitelist `https://nexusrh.ci` et `https://diagnostix.nexusrh.ci`.
- **Headers de sécurité** : `Strict-Transport-Security`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Content-Security-Policy` strict.
- **OpenAPI** : `/api/v1/docs` (Swagger) et `/api/v1/redoc`.

---

## 7. Moteur de calcul fiscal et social CI

> Module : `app/core/ci_fiscal.py`
> **Toutes les valeurs ci-dessous proviennent du cahier des charges, Annexe 1, et du droit fiscal/social ivoirien 2024-2026. Elles sont stockées en BDD (`settings`) et modifiables par l'admin sans redéploiement.**

### 7.1 Barème IGR 2024 (réforme)

```python
IGR_BRACKETS_2024 = [
    # (tranche_min, tranche_max, taux)
    (0,         75_000,    0.00),
    (75_001,    240_000,   0.16),
    (240_001,   800_000,   0.21),
    (800_001,   2_400_000, 0.24),
    (2_400_001, 8_000_000, 0.28),
    (8_000_001, None,      0.32),
]
```

### 7.2 CNPS

```python
CNPS_EMPLOYER_RATE  = 0.105      # 10,5 %
CNPS_EMPLOYEE_RATE  = 0.055      #  5,5 %
CNPS_CEILING        = 600_000    # FCFA / mois (2026)
```

### 7.3 IFC — Indemnité de Fin de Carrière

Basée sur la **Convention Collective Interprofessionnelle de Côte d'Ivoire** :

| Ancienneté | Taux du salaire moyen mensuel des 12 derniers mois |
|---|---|
| 1 à 5 ans | 30 % par année |
| 6 à 10 ans | 35 % par année |
| Au-delà de 10 ans | 40 % par année |

### 7.4 Heures supplémentaires — plafonds légaux CI

```python
HEURES_SUP_PLAFOND_HEBDO   = 15   # h/semaine
HEURES_SUP_PLAFOND_ANNUEL  = 75   # h/an (au-delà : autorisation Inspection du Travail)
HEURES_SUP_MAJORATIONS = {
    "j_ouvrable_15pct":  0.15,    # 41e à 46e h
    "j_ouvrable_50pct":  0.50,    # au-delà de la 46e h
    "nuit_ouvrable":     0.75,
    "j_repos_jour":      0.75,
    "j_repos_nuit":      1.00,
}
```

### 7.5 FDFP

`fdfp_rate = 0.012` (1,2 % de la masse salariale brute).

### 7.6 Tests obligatoires

Chaque fonction du module a un test paramétré (`pytest.mark.parametrize`) couvrant **minimum 8 cas** dont les bornes de chaque tranche IGR, le plafond CNPS atteint et dépassé, IFC à 1 an, 5 ans, 10 ans et 15 ans.

---

## 8. Moteur IA — Analyse, prédiction, recommandations

> **C'est le cœur de la valeur produit.** L'approche est **hybride** : un moteur déterministe (scoring + risque + ML) garantit la reproductibilité et la conformité, et Claude (Anthropic) produit la couche narrative experte, contextualisée et alarmiste/encourageante.

### 8.1 Pipeline en 4 étages

```
┌─────────────────┐   ┌──────────────────┐   ┌───────────────────┐   ┌──────────────┐
│  20 réponses    │ → │ 1. SCORING       │ → │ 2. RISK ENGINE    │ → │ 3. ML MODELS │
│  + métadonnées  │   │  (déterministe)  │   │  (règles + FCFA)  │   │  (sklearn)   │
└─────────────────┘   └──────────────────┘   └───────────────────┘   └──────┬───────┘
                                                                            │
                                              ┌─────────────────────────────┘
                                              ▼
                                       ┌──────────────────┐
                                       │ 4. CLAUDE API    │
                                       │  (narration,     │
                                       │   recos          │
                                       │   stratégiques)  │
                                       └──────────────────┘
```

### 8.2 Étage 1 — Scoring engine déterministe (`scoring_engine.py`)

**Algorithme de pondération (validé par la communauté : moyenne pondérée normalisée, méthode AHP-like simplifiée) :**

1. Pour chaque question `i`, mapper la réponse en valeur numérique :
   - `YES` → 1.0
   - `PARTIAL` → 0.5
   - `MANUAL` → 0.25
   - `NO` → 0.0
   - Question 8 (heures perdues) : `f(h) = max(0, 1 - h/40)` (40h = 0)
2. Score brut catégorie `c` :
   `S_c = (Σ_i poids_i × valeur_i) / (Σ_i poids_i) × 100`
3. Score global :
   `S = Σ_c (poids_categorie_c × S_c)` avec :
   - FISCALE : 0.20
   - SOCIALE : 0.20
   - CONFORMITE : 0.20
   - DIGITALE : 0.40 (objectif central de l'outil = mesurer le gap digital)
4. **Niveau de maturité** :
   - `[0;30[` → **CRITIQUE**
   - `[30;50[` → **ÉMERGENT**
   - `[50;70[` → **STRUCTURÉ**
   - `[70;85[` → **OPTIMISÉ**
   - `[85;100]` → **IA-NATIVE**

### 8.3 Étage 2 — Risk Engine (`risk_engine.py`)

Calcul de l'**exposition financière** en cas de contrôle CNPS / DGI, sur base du sinistre moyen observé chez les clients OpenLab et des barèmes de redressement officiels.

**Règles de risque (toutes paramétrables en BDD) :**

| Code | Condition (réponses) | Sévérité | Impact financier (FCFA) |
|---|---|---|---|
| R-FISC-01 | Q01 ≠ YES | HIGH | `masse_salariale_estimée × 0.08` (redressement IGR) |
| R-SOC-01 | Q02 = MANUAL | HIGH | `effectif × 1_500_000` (IFC mal calculée) |
| R-SOC-02 | Q03 = NO | MEDIUM | `effectif × 200_000` (heures sup. illégales) |
| R-CONF-01 | Q04 = NO | CRITICAL | `5_000_000` forfaitaire (audit non recevable) |
| R-FISC-02 | Q05 ≠ YES | HIGH | `effectif × 50_000 × 12` (DISA non conformes) |
| R-CONF-02 | Q20 = NO | CRITICAL | `3_000_000 à 50_000_000` (sanction ARTCI) |

**Estimation de la masse salariale** : à défaut de donnée, on utilise `effectif × SMIG × 2.5` comme proxy conservateur.

**Score de risque agrégé** : `risk_score = min(100, Σ severity_weight_i × triggered_i)` avec `weight = {LOW:5, MEDIUM:15, HIGH:30, CRITICAL:50}`.

### 8.4 Étage 3 — Modèles ML (`ml_engine.py`)

**Trois modèles sont entraînés offline et chargés au démarrage** (artefacts `.joblib` versionnés en BDD).

#### 8.4.1 Prédiction de non-conformité à 12 mois

- **Algorithme** : `RandomForestClassifier(n_estimators=300, max_depth=8, class_weight='balanced')` — choix justifié par sa robustesse sur petits datasets tabulaires hétérogènes (référence : Breiman 2001, benchmarks Kaggle).
- **Features** (24) : les 20 réponses encodées + 4 méta (taille entreprise, secteur, score_fiscale, score_sociale).
- **Cible** : binaire (1 = redressement CNPS ou DGI dans les 12 mois).
- **Dataset d'entraînement initial** : **dataset synthétique calibré expert** de 5 000 lignes, généré via `scripts/generate_training_data.py` à partir de distributions paramétrées par les consultants OpenLab. La méthodologie est documentée dans `backend/ml/DATASET.md`.
- **Métriques minimales acceptables** (validation croisée 5-fold) : `ROC-AUC ≥ 0.82`, `F1 ≥ 0.75`. Le pipeline CI échoue si ces seuils ne sont pas tenus.

#### 8.4.2 Prédiction du risque de turnover

- **Algorithme** : `GradientBoostingRegressor(n_estimators=200, learning_rate=0.05, max_depth=4)` — éprouvé sur les problématiques RH (cf. études IBM Watson Analytics, Saradhi & Palshikar 2011).
- **Sortie** : probabilité ∈ [0,1].
- **Métriques** : `MAE ≤ 0.08` sur le set de validation.

#### 8.4.3 Calcul du gap digital

- **Méthode** : distance euclidienne pondérée entre le vecteur réponses du client et le vecteur de référence `IA-NATIVE` (toutes réponses = YES). Normalisée sur [0;100] %.
- Pas de ML — calcul déterministe, donc 100 % reproductible.

#### 8.4.4 Garde-fous

- Aucune prédiction n'est exposée si la confiance du modèle (`predict_proba`) est `< 0.60` → on affiche "Donnée insuffisante".
- Les artefacts ML sont **versionnés** ; chaque rapport stocke le hash du modèle utilisé.

### 8.5 Étage 4 — Claude API (`ai_service.py`)

**Modèle** : `claude-opus-4-7` (puissance maximale pour l'analyse experte).

**Prompt système** (stocké dans `app/core/prompts/expert_system.py`, identique à l'Annexe 1 du cahier des charges, **enrichi** des résultats des étages 1-3) :

```
Tu es l'Expert IA de NexusRH, spécialisé dans le droit du travail, la fiscalité
et la transformation digitale en Côte d'Ivoire.

CONTEXTE LÉGAL DE RÉFÉRENCE (2024-2026) :
- Réforme fiscale IGR 2024 (Annexe fiscale CGI CI)
- CNPS : 10,5 % employeur / 5,5 % salarié, plafond 600 000 FCFA
- IFC : Convention Collective Interprofessionnelle CI
- Loi ARTCI n°2013-450

DONNÉES CALCULÉES (ne pas recalculer, à interpréter) :
- Score global : {global_score}/100
- Niveau de maturité : {maturity_level}
- Scores par catégorie : {scores_by_category}
- Risques détectés (déterministes) : {risks_detected}
- Exposition financière estimée : {financial_exposure} FCFA
- Probabilité de non-conformité 12 mois : {non_compliance_proba}
- Gap digital : {digital_gap_pct} %

TA MISSION : produire un JSON strict avec la structure suivante (aucun texte hors JSON) :
{
  "executive_summary": "<3 phrases percutantes>",
  "risk_narrative":   "<analyse approfondie des risques, ton alarmiste si HIGH/CRITICAL>",
  "digital_gap_narrative": "<comparaison concrète au standard IA-Native>",
  "recommendations": [
    {
      "priority": 1,
      "title": "...",
      "description": "...",
      "expected_gain_fcfa": <int>,
      "implementation_weeks": <int>,
      "nexusrh_module": "<nom du module SaaS NexusRH qui résout le problème>"
    },
    { "priority": 2, ... },
    { "priority": 3, ... }
  ],
  "key_takeaway": "<phrase d'appel à l'action finale, encourageante>"
}

TON : professionnel, expert, alarmiste sur les risques légaux,
encourageant sur les opportunités de modernisation.
```

**Garanties** :
- Appel API avec `temperature=0.3` (déterminisme acceptable).
- `max_tokens=2000`.
- **Validation Pydantic** stricte de la sortie ; en cas d'échec, **1 retry** avec un prompt correctif, puis fallback sur un template statique pré-rédigé pour ne **jamais** échouer la génération du rapport.
- **Cache Redis** (clé = hash SHA-256 des entrées) : un même set de réponses ne consomme pas deux fois l'API.
- **Timeout** : 30 s. **Coût loggé** par requête (tokens in/out).

### 8.6 Tests obligatoires du moteur IA

- 100 % de couverture sur `scoring_engine`, `risk_engine`, `ml_engine`.
- Sur `ai_service` : tests avec **mock de l'API Anthropic** (réponses canned), test du fallback, test du cache.
- Test d'**invariance** : 3 jeux de réponses fixes → scores attendus à la décimale près (snapshot tests).

---

## 9. Frontend — UX, UI, parcours

### 9.1 Principes de design

- **Charte** : reprise stricte de la charte NexusRH (orange `#FF5500` accent, deep orange `#CC3300`, noir `#0A0A0A`, gris `#F5F5F5`, typographie sans-serif moderne — `Inter` + `Space Grotesk`). Logo officiel : `public/openlab.png`.
- **Esthétique** : épurée, premium, beaucoup d'espace blanc, animations subtiles (Framer Motion, durées 200-400 ms, easing `ease-out`).
- **Mobile-first** : responsive parfait de 360 px à 4K.
- **Accessibilité** : WCAG 2.1 AA — contrastes, focus visibles, navigation clavier complète, ARIA labels.

### 9.2 Parcours utilisateur

#### Écran 1 — Landing (`/`)
- Hero avec proposition de valeur en 1 phrase + CTA "Démarrer mon diagnostic gratuit (5 min)".
- Bandeau "Conforme ARTCI — Aucune donnée nominative stockée".
- 3 cartes bénéfices (risques chiffrés, gap digital, recos).
- Témoignages (vide en V1, structure prévue).
- Footer : mentions légales (Annexe 4 du cahier des charges, **mot pour mot**).

#### Écran 2 — Pré-questionnaire (`/diagnostic/start`)
- 3 champs : taille entreprise (select), secteur (select), email (optionnel).
- Checkbox de consentement explicite (**pré-décochée** — exigence ARTCI).
- Bouton "Commencer".

#### Écran 3 — Questionnaire (`/diagnostic/{session_id}/q/{n}`)
- **Une seule question par écran** (règle UX cardinale : limite la charge cognitive — Hick's Law, Miller 7±2).
- Barre de progression fluide en haut (`[██████░░░░] 6/20`).
- Animation `slide-in-from-right` à chaque question, `slide-out-to-left` au passage.
- Boutons de réponse en grandes cartes cliquables (min `48 px` de hauteur — Fitts).
- Navigation : `← Précédent` (sauf Q1) / `Suivant →` (désactivé tant que pas de réponse) / barre d'espace pour valider.
- Auto-save sur chaque réponse (POST silencieux, indicateur "Enregistré" discret).
- Texte d'aide `?` cliquable révélant `help_text`.
- **Estimation du temps restant** affichée discrètement en bas.

#### Écran 4 — Génération (`/diagnostic/{session_id}/generating`)
- Loader élégant avec étapes affichées dynamiquement :
  1. ✅ Calcul du score de maturité
  2. ✅ Évaluation des risques fiscaux & sociaux
  3. ⏳ Analyse experte par IA
  4. ⏳ Génération de votre rapport personnalisé
- Polling toutes les 2 s sur `GET /reports/{id}`.
- Durée cible perçue : 10-15 s. Si > 30 s, message rassurant.

#### Écran 5 — Rapport (`/diagnostic/report/{report_id}`)
- En-tête : score global en jauge animée (Recharts `RadialBar`), niveau de maturité en gros.
- 4 mini-jauges pour les sous-scores.
- Section "Synthèse exécutive" (texte IA).
- Section "Risques identifiés" : matrice impact/probabilité (scatter chart).
- Section "Gap digital" : radar chart vs standard IA-Native.
- Section "3 recommandations stratégiques" : cartes ordonnées.
- 3 boutons : `📥 Télécharger le PDF`, `📧 Recevoir par email`, `📞 Demander une démo NexusRH`.

#### Écran 6 — Espace admin (`/admin`)
- Login sobre (email + mot de passe + 2FA TOTP optionnel).
- Dashboard : KPIs (nb diagnostics, score moyen, distribution maturité, taux complétion).
- Tableau des leads opt-in (export CSV).
- Éditeur de questions (drag-and-drop pour l'ordre, modale d'édition).
- Éditeur de paramètres (taux fiscaux/sociaux).
- Visualisation du journal d'audit.

### 9.3 Composants critiques

Chaque composant a un test unitaire (Vitest + Testing Library) et un test E2E (Playwright) pour le parcours complet.

---

## 10. Génération du rapport PDF

### 10.1 Stack

`WeasyPrint 62+` rend un template Jinja2 HTML/CSS optimisé pour l'impression A4.

### 10.2 Structure du rapport (10-12 pages)

1. **Page de garde** : logo NexusRH, titre "Rapport Nexus-Diagnostix", nom secteur/taille, date, ID rapport.
2. **Synthèse exécutive** (1 page) : score global en jauge, niveau de maturité, paragraphe IA.
3. **Tableau de bord** (1 page) : 4 sous-scores, gap digital, exposition financière.
4. **Analyse des risques** (2-3 pages) : tableau détaillé des risques détectés avec sévérité, description, impact FCFA, référence légale.
5. **Gap digital** (1 page) : radar chart, narratif IA, comparaison "vous vs standard IA-Native".
6. **Prédictions** (1 page) : probabilité de non-conformité 12 mois, risque turnover, intervalle de confiance.
7. **Recommandations stratégiques** (2 pages) : 3 cartes détaillées avec ROI estimé et timeline.
8. **Plan d'action 90 jours** (1 page) : roadmap visuelle (Gantt léger).
9. **Annexes** : méthodologie de scoring, références légales, mentions ARTCI.

### 10.3 Design

- Charte stricte NexusRH (orange, noir, gris).
- Typographie : `Inter` (corps) + `Space Grotesk` (titres).
- Headers / footers avec pagination, ID rapport, date.
- QR code en dernière page → URL signée du rapport en ligne.
- Watermark `CONFIDENTIEL` en filigrane discret.

### 10.4 Diffusion

- Stockage local chiffré (`/var/data/reports/{report_id}.pdf`, AES-256 at rest).
- URL signée HMAC-SHA256, TTL 7 jours (variable `PDF_URL_TTL_DAYS`).
- Envoi par email via **SMTP aiosmtplib** (défaut dev/staging) ou SendGrid (production, activé si `SENDGRID_API_KEY` défini). Port 587 = STARTTLS, port 465 = SSL direct.
- **Bouton "Partage 1-clic"** dans l'UI : copie un lien signé dans le presse-papier.

---

## 11. Sécurité et conformité ARTCI

### 11.1 Conformité Loi 2013-450 (ARTCI)

- **Mention légale** affichée mot pour mot (Annexe 4) en footer et avant tout consentement.
- **Consentement explicite** : checkbox pré-décochée, action positive obligatoire.
- **Anonymisation** : aucune donnée nominative requise pour le diagnostic ; seul l'email (chiffré AES-256) est stocké et **uniquement** si opt-in.
- **Droit d'accès / suppression** : route publique `POST /privacy/erasure-request` avec validation par email vers `dpo@openlabconsulting.com`. Suppression effective sous 30 jours, traçabilité dans `audit_logs`.
- **Rétention** : sessions non finalisées purgées après 30 jours ; logs 6 mois ; rapports 24 mois (configurable).

### 11.2 Sécurité technique

| Mesure | Implémentation |
|---|---|
| Transport | TLS 1.3 obligatoire, HSTS preload |
| Mot de passe admin | bcrypt cost 12, politique 12 caractères mini, rotation 90 j |
| Sessions | JWT signé HS256, secret 256 bits rotaté trimestriellement |
| 2FA admin | TOTP (RFC 6238) optionnel mais recommandé |
| Chiffrement BDD | AES-256 sur disque (LUKS) + colonnes sensibles chiffrées applicativement (Fernet) |
| Rate limiting | Redis token bucket, 60/min public, 10/min sur `/auth/login` |
| Anti-CSRF | SameSite=Strict + token CSRF côté admin |
| Anti-bot | hCaptcha sur le démarrage de session |
| Logs | Centralisés, hashs IP (jamais d'IP en clair), rotation, intégrité (signature) |
| Backups | Quotidiens chiffrés, conservation 30 jours, tests de restauration mensuels |
| Secrets | Variables d'environnement uniquement, **jamais** committés. `.env.example` documenté |
| Dépendances | `pip-audit` + `npm audit` en CI, blocage sur CVE HIGH+ |

### 11.3 Headers HTTP imposés

```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
```

---

## 12. Stratégie de tests — couverture 100 %

### 12.1 Pyramide de tests

```
                ┌─────────────┐
                │  E2E (10%)  │  Playwright — 8 scénarios critiques
                └─────────────┘
              ┌─────────────────┐
              │ Integration(20%)│  pytest — API endpoints, DB
              └─────────────────┘
          ┌───────────────────────┐
          │     Unit (70%)        │  pytest + Vitest — toute la logique
          └───────────────────────┘
```

### 12.2 Règles strictes

- **Couverture exigée : 100 %** sur tous les modules métier (`services/`, `core/`, `api/v1/`). Mesurée par `pytest --cov=app --cov-fail-under=100`.
- **Mutation testing** sur les modules critiques (`scoring_engine`, `risk_engine`, `ci_fiscal`) avec `mutmut` — survie ≤ 5 %.
- **Tests paramétrés** systématiques pour tout calcul (`pytest.mark.parametrize`).
- **Pas de mock excessif** : préférer des tests d'intégration avec une **vraie BDD PostgreSQL en container** (`testcontainers-python`).
- **Mocks contrôlés uniquement pour** : Anthropic API, SMTP, Redis (avec `fakeredis`).
- **Fixtures déterministes** : `faker` avec seed fixe.
- **Tests E2E** dans CI sur 3 navigateurs (Chromium, Firefox, WebKit).

### 12.3 Scénarios E2E obligatoires

1. Visiteur complète les 20 questions et reçoit son PDF.
2. Visiteur abandonne en cours de route et reprend (résumabilité).
3. Visiteur tente de finaliser sans avoir répondu → erreur claire.
4. Admin se connecte, modifie une question, déconnecte, le changement est visible côté public.
5. Admin modifie le taux CNPS → un nouveau diagnostic reflète le changement.
6. Tentative de force brute sur `/auth/login` → blocage après 5 essais.
7. Génération PDF échoue (Claude API down) → fallback statique fonctionne.
8. Téléchargement PDF avec token expiré → erreur 401.

### 12.4 CI — règles de blocage

Le merge est **interdit** si :
- couverture < 100 % sur les modules métier ;
- ruff / mypy / eslint / tsc remontent une erreur ;
- un test échoue (y compris flaky) ;
- une CVE HIGH+ est détectée ;
- `pytest --cov-fail-under=100` échoue ;
- les seuils ML (ROC-AUC ≥ 0.82, MAE ≤ 0.08) ne sont pas tenus.

---

## 13. DevOps, CI/CD, hébergement

### 13.1 Environnements

| Env | URL | BDD | Branche |
|---|---|---|---|
| `dev` | localhost (docker-compose) | postgres local | feature/* |
| `staging` | `https://staging.diagnostix.nexusrh.ci` | RDS / managed | `develop` |
| `prod` | `https://diagnostix.nexusrh.ci` | RDS / managed | `main` |

### 13.2 Pipeline GitHub Actions (`.github/workflows/ci.yml`)

```
on: [push, pull_request]

jobs:
  backend-quality:
    - ruff check
    - mypy --strict
    - pip-audit
    - pytest --cov=app --cov-fail-under=100
    - mutmut run (modules critiques)

  frontend-quality:
    - eslint
    - tsc --noEmit
    - npm audit --audit-level=high
    - vitest --coverage  (seuil 100% sur logique métier)

  e2e:
    needs: [backend-quality, frontend-quality]
    - docker-compose up -d
    - playwright test

  build:
    needs: [e2e]
    - docker build backend / frontend
    - push to registry
```

### 13.3 Déploiement

- Docker Compose en staging, **Kubernetes (k3s)** en prod si effectif > 50k diagnostics/mois, sinon Docker Compose suffit.
- **Blue-green deployment** : zéro downtime.
- **Migrations Alembic** appliquées automatiquement avec verrou de migration (lock advisory PostgreSQL).
- **Healthchecks** : `/healthz` (liveness) et `/readyz` (readiness, vérifie BDD + Redis + Anthropic).
- **Monitoring** : Prometheus + Grafana, alerting sur taux d'erreur 5xx > 1 %, latence P95 > 1 s, échec génération PDF > 2 % .
- **Logs** : JSON structuré → Loki ou ELK.

---

## 14. Plan d'exécution séquentiel pour Claude Code

> **Règle absolue : chaque étape se termine par une suite de tests verts à 100 %. Aucune étape n'est commencée tant que la précédente n'est pas validée.**
>
> **Légende :** ✅ Terminé · 🔄 Partiel · ⏳ À faire

### ✅ Sprint 0 — Bootstrap (1 jour)
1. Créer la structure de dépôt complète (cf. §4).
2. Initialiser `pyproject.toml`, `package.json`, `docker-compose.yml`, `.env.example`.
3. Vérifier : `docker-compose up` lance Postgres + Redis sans erreur.

### ✅ Sprint 1 — Modèles et migrations (1 jour)
1. Implémenter tous les modèles SQLAlchemy (§5.1).
2. Générer les migrations Alembic (révisions 0001 + 0002).
3. Implémenter le seed (questions de l'Annexe 2 + settings + admin).
4. Scripts utilitaires : `seed_initial_data.py`, `reset_admin_password.py`.

### ✅ Sprint 2 — Moteur fiscal CI (1 jour)
1. Implémenter `core/ci_fiscal.py` : IGR, CNPS, IFC, heures sup., FDFP.
2. Tests paramétrés : ≥ 8 cas par fonction, couverture 100 %.

### ✅ Sprint 3 — Scoring & Risk Engine (2 jours)
1. Implémenter `services/scoring_engine.py` (§8.2).
2. Implémenter `services/risk_engine.py` (§8.3).
3. Tests : snapshot tests sur 5 jeux de réponses de référence (cas CRITIQUE → IA-NATIVE), couverture 100 %.

### ✅ Sprint 4 — ML Engine (2 jours)
1. Script `scripts/generate_training_data.py` produisant 5 000 lignes synthétiques calibrées.
2. Entraînement offline, validation cross-val 5-fold, export `.joblib`.
3. Implémenter `services/ml_engine.py` (chargement, prédiction, garde-fous confidence < 0.60).
4. Tests : seuils ROC-AUC ≥ 0.82, MAE ≤ 0.08, prédictions reproductibles avec seed.

### ✅ Sprint 5 — AI Service Claude (1 jour)
1. Implémenter `services/ai_service.py` avec prompt système (§8.5).
2. Validation Pydantic stricte de la sortie JSON + fallback statique.
3. Cache Redis (clé = SHA-256 des inputs), 1 retry, timeout 30 s.
4. Tests avec mock de l'API Anthropic.

### ✅ Sprint 6 — API REST publique (2 jours)
1. Endpoints `/sessions`, `/responses`, `/finalize`, `/reports`, `/reports/{id}/pdf`, `/reports/{id}/send`.
2. Rate limiting, validation Pydantic v2, gestion d'erreurs RFC 7807.
3. Finalize idempotent (React StrictMode double-fire), normalisation `FREE_NUMERIC` côté schema.
4. Gestionnaire d'exception générique assurant les headers CORS sur toutes les 500.

### ✅ Sprint 7 — Génération PDF (2 jours)
1. Template Jinja2 `templates/report.html` (§10.2) avec CSS print.
2. `services/report_service.py` : rendu WeasyPrint, stockage `/var/data/reports/`, URL signée HMAC.
3. Tests : génération de rapports de référence, extraction texte, vérification signature.

### ✅ Sprint 8 — Email (0,5 jour)
1. `services/email_service.py` : backend SMTP aiosmtplib (STARTTLS sur port 587, SSL sur 465) ou SendGrid.
2. Template HTML responsive + version plain-text.
3. Tests avec mock SMTP (aiosmtplib patché).

### ✅ Sprint 9 — Auth & Admin API (1,5 jour)
1. `/auth/login` (JWT HS256, TTL 8h), `/auth/refresh`.
2. Endpoints admin complets (§6.2) : questions, settings, stats, leads, audit.
3. Politique mot de passe bcrypt cost 12, protection bruteforce (5 essais → verrouillage).
4. Script `reset_admin_password.py` pour déblocage.

### ✅ Sprint 10 — Frontend public (3 jours)
1. Landing page charte OpenLab (orange #FF5500, Space Grotesk, Inter).
2. Parcours questionnaire (1 question/écran, animations Framer Motion, auto-save silencieux).
3. Écran de génération avec polling toutes les 2 s + étapes dynamiques.
4. Rapport interactif : scores, risques, recommandations, boutons PDF/email.
5. Questionnaire responsive keyboard shortcuts (touches 1/2/3, Entrée).

### ✅ Sprint 11 — Frontend admin (2 jours)
1. Login sobre avec protection bruteforce côté client.
2. Dashboard KPIs + 5 onglets (dashboard, questions, paramètres, leads, audit).
3. Modale d'édition des questions, toggle actif/inactif, export CSV des leads.
4. Éditeur JSON des paramètres fiscaux/sociaux.

### 🔄 Sprint 12 — Sécurité & conformité (1 jour) — EN COURS
1. ✅ Headers HTTP sécurité via middleware FastAPI (`main.py`).
2. ✅ CORS contrôlé par `ALLOWED_ORIGINS` (`.env`).
3. ✅ Gestionnaire d'exception global (CORS sur toutes les 500).
4. ⏳ Route `POST /privacy/erasure-request` (effacement données ARTCI).
5. ⏳ Pages dédiées mentions légales / CGU.
6. ⏳ Audit `pip-audit`, `npm audit` automatisé en CI.

### 🔄 Sprint 13 — CI/CD & déploiement (1 jour) — EN COURS
1. ✅ Workflow GitHub Actions `.github/workflows/ci.yml`.
2. ✅ Dockerfile multi-stage (backend dev + prod, frontend dev + prod).
3. ✅ `docker-compose.prod.yml` configuré.
4. ⏳ Déploiement staging automatique.
5. ⏳ Tests E2E sur staging.

### ⏳ Sprint 14 — Recette & durcissement (2 jours)
1. Tests de charge (`locust`) : 100 sessions concurrentes.
2. Pentest light (OWASP ZAP).
3. Vérification couverture 100 % sur tous les modules.
4. Documentation utilisateur complète + vidéo de démo.

**Total : ≈ 22 jours homme** — livraison cible **30 juin 2026**.

---

## 15. Critères d'acceptation finaux

L'application est livrée **uniquement** si **tous** les critères suivants sont satisfaits :

- [x] Le parcours visiteur complet (landing → questionnaire → rapport JSON + email) fonctionne de bout en bout.
- [x] Les 20 questions du cahier des charges (Annexe 2) sont présentes avec les pondérations et types exacts.
- [x] Le score global est calculé selon §8.2 et reproductible à la décimale près (snapshot tests).
- [x] Le rapport PDF est généré via WeasyPrint (template Jinja2 + CSS print), URL signée HMAC.
- [x] Les modèles ML atteignent les seuils §8.4 sur le set de validation (ROC-AUC ≥ 0.82, MAE ≤ 0.08).
- [x] L'analyse Claude est strictement validée par Pydantic, le fallback statique fonctionne.
- [x] Le compte admin permet d'éditer questions et taux sans redéploiement.
- [x] Email SMTP opérationnel (Gmail STARTTLS port 587) avec template HTML responsive.
- [ ] **Couverture de tests = 100 %** sur les modules métier, **mutation score ≥ 95 %** sur les modules critiques.
- [ ] Les 8 scénarios E2E passent sur Chromium, Firefox, WebKit (Playwright).
- [ ] Conformité ARTCI complète : route `POST /privacy/erasure-request` opérationnelle, pages CGU.
- [ ] Headers de sécurité au niveau A+ sur securityheaders.com (en prod avec TLS).
- [ ] CI bloque tout merge ne respectant pas les règles §12.4.
- [x] Documentation : `README.md` complet, OpenAPI accessible à `/api/v1/docs`.

---

> **Signature d'engagement :** Toute déviation par rapport à ce document doit faire l'objet d'une décision tracée dans un fichier `DECISIONS.md` à la racine du dépôt. Aucun raccourci silencieux n'est toléré.
>
> *Document maintenu par OpenLab Consulting — version 1.0 — Mai 2026.*
