# Architecture — Nexus-Diagnostix

## Vue d'ensemble

```
┌──────────────────────────────────────────────────────────────┐
│                     CLIENT (navigateur)                      │
│   React 18 + Vite + TS + Tailwind + shadcn/ui                │
└────────────────────────────┬─────────────────────────────────┘
                             │ HTTPS / TLS 1.3
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                   API (FastAPI / Python 3.11)                │
│   Routeur /api/v1                                            │
│   Services : Scoring · Risk · ML · IA · PDF · Email · Auth   │
└──────────┬──────────────────────────┬────────────────────────┘
           │                          │
           ▼                          ▼
┌────────────────────┐   ┌────────────────────────────────────┐
│   PostgreSQL 16    │   │   Anthropic Claude API             │
│   AES-256 at rest  │   │   claude-opus-4-7 (analyse)        │
└────────────────────┘   └────────────────────────────────────┘
           │
           ▼
┌────────────────────┐
│   Redis 7          │
│   Rate-limit, cache│
└────────────────────┘
```

## Pipeline IA en 4 étages

1. **Scoring déterministe** — moyenne pondérée par catégorie
2. **Risk engine** — règles métier → exposition FCFA
3. **ML** — Random Forest (non-conformité) + Gradient Boosting (turnover)
4. **Claude API** — narration experte JSON validée Pydantic

Voir [`../CLAUDE.md`](../CLAUDE.md) §8 pour le détail.

## Décisions techniques majeures

| Décision | Justification |
|---|---|
| FastAPI async | Performances, OpenAPI auto, validation Pydantic native |
| SQLAlchemy 2 async | ORM moderne, type-safe, async/await |
| WeasyPrint | HTML→PDF de qualité supérieure à wkhtmltopdf, CSS print riche |
| Random Forest + GBM | Robuste sur tabulaire petit dataset, explicable |
| Hébergement local CI | Souveraineté + conformité ARTCI |
| JWT stateless | Scalabilité horizontale sans sticky sessions |
