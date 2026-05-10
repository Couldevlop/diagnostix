# API REST — Nexus-Diagnostix

Documentation interactive complète : `/api/v1/docs` (Swagger) et `/api/v1/redoc`.

## Convention

- Préfixe : `/api/v1`
- Format : JSON UTF-8
- Erreurs : RFC 7807 (Problem Details)
- Auth admin : `Authorization: Bearer <JWT>`

## Endpoints publics

| Méthode | Route | Description |
|---|---|---|
| `POST` | `/sessions` | Démarrer une session de diagnostic |
| `GET`  | `/sessions/{id}/questions` | Liste des questions actives |
| `POST` | `/sessions/{id}/responses` | Enregistrer une réponse (idempotent) |
| `POST` | `/sessions/{id}/finalize` | Verrouiller et générer le rapport |
| `GET`  | `/reports/{id}` | Rapport JSON |
| `GET`  | `/reports/{id}/pdf` | Téléchargement PDF (token signé) |
| `POST` | `/reports/{id}/send` | Envoi par email |

## Endpoints admin

| Méthode | Route | Description |
|---|---|---|
| `POST` | `/auth/login` | JWT (email + password) |
| `POST` | `/auth/refresh` | Refresh token |
| `GET`  | `/admin/questions` | Lister/éditer les questions |
| `GET`  | `/admin/settings` | Paramètres (taux, plafonds) |
| `GET`  | `/admin/stats` | KPIs agrégés |
| `GET`  | `/admin/audit-logs` | Journal d'audit |

Voir [`../CLAUDE.md`](../CLAUDE.md) §6 pour les schémas request/response complets.
