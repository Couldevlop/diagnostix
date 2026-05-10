# DECISIONS.md — Nexus-Diagnostix

> Conformément à la règle d'engagement de `CLAUDE.md`, ce fichier trace toutes les déviations
> par rapport à la spécification d'origine. Chaque décision est datée et justifiée.

---

## D-001 · Couleur orange de la charte

**Date :** 2026-05-08  
**Section CLAUDE.md concernée :** §9.1  
**Déviation :** La spec mentionnait `#FF5A1F` comme couleur orange accent.

**Décision :** Utilisation de `#FF5500` (orange OpenLab réel, extrait du logo `OPENLAB.png`) et `#CC3300` comme deep orange.

**Justification :** La couleur `#FF5A1F` était une approximation. Le logo officiel fourni par OpenLab Consulting utilise `#FF5500`. La cohérence visuelle avec le logo prime sur la spec initiale.

---

## D-002 · Backend email : SMTP prioritaire sur SendGrid

**Date :** 2026-05-08  
**Section CLAUDE.md concernée :** §10.4  
**Déviation :** La spec indiquait SendGrid comme backend email principal.

**Décision :** SMTP via `aiosmtplib` est le backend par défaut (Gmail STARTTLS sur port 587). SendGrid est supporté mais optionnel (activé uniquement si `SENDGRID_API_KEY` est défini).

**Justification :** En dev/staging, un compte Gmail avec App Password suffit sans compte SendGrid payant. L'architecture dual-backend (SMTP/SendGrid) est maintenue pour la production.

**Impact technique :** `email_service.py` détecte automatiquement le protocole selon le port : port 587 → STARTTLS (`start_tls=True, use_tls=False`), port 465 → SSL direct.

---

## D-003 · Endpoint finalize rendu idempotent

**Date :** 2026-05-09  
**Section CLAUDE.md concernée :** §6.1 `POST /sessions/{session_id}/finalize`  
**Déviation :** La spec ne précisait pas le comportement sur double-appel.

**Décision :** Si la session est déjà `COMPLETED`, le endpoint retourne le rapport existant (200) au lieu de lever une `ConflictError` (409).

**Justification :** React 18 StrictMode en développement déclenche `useEffect` deux fois. Le double appel à `/finalize` causait un 409 qui bloquait la navigation vers le rapport. L'idempotence est le comportement attendu pour les endpoints d'écriture (cf. §2.1 "Idempotence des endpoints").

---

## D-004 · Normalisation des réponses FREE_NUMERIC côté schéma

**Date :** 2026-05-09  
**Section CLAUDE.md concernée :** §6.1 `POST /sessions/{id}/responses`  
**Déviation :** La spec indiquait que le frontend devait envoyer `answer_value="FREE_NUMERIC"`.

**Décision :** `ResponseIn.model_post_init` normalise automatiquement : si `answer_value` n'est pas dans `{YES, NO, PARTIAL, MANUAL, FREE_NUMERIC}`, il tente une conversion `float()`. Si succès → `answer_value="FREE_NUMERIC"`, `answer_numeric=valeur`. Si échec → `ValueError`.

**Justification :** Double protection : le frontend envoie désormais correctement `answer_value="FREE_NUMERIC"` + `answer_numeric`, mais la normalisation côté backend évite toute régression si un client envoie la valeur brute.

---

## D-005 · Gestionnaire d'exception global pour CORS sur les 500

**Date :** 2026-05-09  
**Section CLAUDE.md concernée :** §6.3 (CORS), §11.2  
**Déviation :** Non documenté dans la spec.

**Décision :** Ajout d'un `@app.exception_handler(Exception)` dans `main.py` qui intercepte toutes les exceptions non gérées et retourne une `JSONResponse` 500 structurée (RFC 7807). Cela garantit que les headers CORS sont toujours présents, même sur les erreurs non anticipées.

**Justification :** FastAPI bypass le middleware CORS lorsqu'une exception non gérée remonte. Sans ce handler, les erreurs 500 provoquaient des `ERR_FAILED` côté navigateur masquant le vrai message d'erreur.

---

## D-006 · Migration 0002 — ajout colonne `status` sur `reports`

**Date :** 2026-05-08  
**Section CLAUDE.md concernée :** §5.1 (schéma PostgreSQL)  
**Déviation :** La migration initiale (0001) n'incluait pas la colonne `status VARCHAR(20)` sur la table `reports`.

**Décision :** Création de la migration `0002_add_reports_status.py` : `ALTER TABLE reports ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'READY'`.

**Justification :** La colonne `status` est nécessaire pour le polling (GENERATING → READY → FAILED) et pour les requêtes admin (`avg_score WHERE status='READY'`). L'omission était une erreur dans la migration initiale.

---

## D-007 · Drag-and-drop admin non implémenté (V1)

**Date :** 2026-05-10  
**Section CLAUDE.md concernée :** §9.2 Écran 6 — "drag-and-drop pour l'ordre"  
**Déviation :** L'éditeur de questions admin n'a pas de drag-and-drop.

**Décision :** L'ordre des questions est modifiable via le champ `order` directement en base. L'interface admin propose l'édition du libellé, du poids et du texte d'aide via une modale, ainsi que le toggle actif/inactif.

**Justification :** Le drag-and-drop (ex. `@dnd-kit/core`) représente un surcoût de complexité sans valeur critique pour la V1. Les 20 questions ont un ordre fixe défini au seed ; les réordres sont rares et peuvent être faits par migration ou script.

**Prévu pour :** V1.1 si besoin exprimé.

---

## D-008 · 2FA TOTP non implémenté (V1)

**Date :** 2026-05-10  
**Section CLAUDE.md concernée :** §9.2 Écran 6, §11.2  
**Déviation :** La spec mentionnait "2FA TOTP (RFC 6238) optionnel mais recommandé".

**Décision :** Non implémenté en V1. La protection bruteforce (5 tentatives → verrouillage + `locked_until`) et les mots de passe forts (bcrypt cost 12) couvrent le risque immédiat.

**Prévu pour :** V1.2 avec `pyotp` + QR code d'activation.

---

## D-009 · Route `/privacy/erasure-request` non implémentée (V1)

**Date :** 2026-05-10  
**Section CLAUDE.md concernée :** §11.1  
**Déviation :** La route ARTCI d'effacement n'est pas encore créée.

**Statut :** Sprint 12 en cours — à implémenter avant la mise en production.

**Processus provisoire :** Les demandes d'effacement sont traitées manuellement sur `dpo@openlabconsulting.com` dans un délai de 30 jours, conformément à la Loi 2013-450.

---

*Document maintenu par OpenLab Consulting — mis à jour au fur et à mesure des décisions de développement.*
