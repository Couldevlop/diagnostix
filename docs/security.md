# Sécurité & Conformité — Nexus-Diagnostix

## Loi ARTCI n°2013-450 (Protection des données — Côte d'Ivoire)

- ✅ **Consentement explicite** — checkbox pré-décochée pour l'email
- ✅ **Anonymisation** — aucune donnée nominative requise pour le diagnostic
- ✅ **Mention légale** affichée mot pour mot en footer
- ✅ **Droit d'accès et d'effacement** via `dpo@openlabconsulting.com`
- ✅ **Hash IP** (SHA-256) — jamais d'IP en clair dans les logs
- ✅ **Rétention** : sessions 30 j, logs 6 mois, rapports 24 mois

## Mesures techniques

| Domaine | Mesure |
|---|---|
| Transport | TLS 1.3, HSTS preload |
| Mots de passe | bcrypt cost 12, ≥ 12 caractères, rotation 90 j |
| Session admin | JWT HS256, secret 256 bits |
| 2FA | TOTP (RFC 6238) optionnel |
| BDD | AES-256 at rest, colonnes sensibles chiffrées (Fernet) |
| Rate limit | Token bucket Redis (60/min public, 10/min login) |
| CSRF admin | SameSite=Strict + token CSRF |
| Anti-bot | hCaptcha au démarrage de session |
| Backups | Quotidiens chiffrés, rétention 30 j, restauration testée |

## Headers HTTP

```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
Content-Security-Policy: default-src 'self'; script-src 'self'; …
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
```

Cible : note **A+** sur securityheaders.com.

## Modèle de menaces

Voir [`../CLAUDE.md`](../CLAUDE.md) §11.
