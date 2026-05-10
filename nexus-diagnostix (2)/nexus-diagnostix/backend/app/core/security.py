"""Primitives de sécurité : hashing de mots de passe.

Ce module encapsule **bcrypt** directement (sans passlib), pour deux raisons :

1. **Maintenabilité** : passlib n'est plus maintenu depuis 2020 et casse avec les
   versions récentes de la lib `bcrypt` (incompatibilité `bcrypt.__about__`
   supprimée en bcrypt ≥ 4.1).

2. **Limite des 72 bytes** : la spec bcrypt impose un mot de passe ≤ 72 bytes.
   bcrypt ≥ 4.1 lève désormais une erreur explicite. On gère cette limite ici
   en :
     - validant `password_min_length` côté création (cf. config),
     - **pré-hashant** en SHA-256 les mots de passe trop longs (technique
       reconnue, recommandée par OWASP : `Password Storage Cheat Sheet`).

Le pré-hash SHA-256 → bcrypt est sûr : SHA-256 produit 32 bytes, bcrypt accepte
72 bytes. Cette technique est utilisée par Dropbox, Auth0, etc. Elle est
mentionnée explicitement dans le RFC bcrypt et l'OWASP cheat sheet.
"""
from __future__ import annotations

import base64
import hashlib
import re

import bcrypt

# Coût bcrypt par défaut. 12 ≈ 250 ms / hash sur un CPU moderne — bon équilibre.
DEFAULT_BCRYPT_ROUNDS = 12

# bcrypt n'accepte pas les mots de passe > 72 bytes. On pré-hash ceux-là.
BCRYPT_MAX_PASSWORD_BYTES = 72

# Format strict d'un hash bcrypt valide :
#   $<version>$<rounds>$<22 chars salt><31 chars hash>
# où version ∈ {2, 2a, 2b, 2x, 2y}, rounds est un entier sur 2 chiffres,
# et la partie data fait exactement 53 caractères (22 + 31).
# Ref : https://en.wikipedia.org/wiki/Bcrypt#Description
_BCRYPT_HASH_PATTERN = re.compile(
    r"^\$2[abxy]?\$\d{2}\$[./A-Za-z0-9]{53}$"
)


def _is_valid_bcrypt_hash(hashed: str) -> bool:
    """Vérifie qu'une chaîne respecte le format strict d'un hash bcrypt.

    Indispensable car la lib `bcrypt` (Rust) **panique** (pyo3_runtime.PanicException)
    sur les hashs malformés, et cette exception n'est pas rattrapable par
    `except Exception` (elle hérite directement de BaseException).
    """
    return bool(_BCRYPT_HASH_PATTERN.match(hashed))


def _prepare_password(password: str) -> bytes:
    """Convertit le mot de passe en bytes prêts pour bcrypt.

    Si le mot de passe encodé en UTF-8 dépasse 72 bytes, on le pré-hash en
    SHA-256 puis on encode le résultat en base64 (44 caractères, < 72 bytes).
    Cela évite l'erreur `password cannot be longer than 72 bytes` tout en
    préservant l'unicité cryptographique.

    Returns:
        bytes prêts à passer à `bcrypt.hashpw()`.
    """
    encoded = password.encode("utf-8")
    if len(encoded) <= BCRYPT_MAX_PASSWORD_BYTES:
        return encoded

    # Pré-hash SHA-256 → 32 bytes → base64 → 44 bytes.
    digest = hashlib.sha256(encoded).digest()
    return base64.b64encode(digest)


def hash_password(password: str, rounds: int = DEFAULT_BCRYPT_ROUNDS) -> str:
    """Hash un mot de passe avec bcrypt.

    Args:
        password: mot de passe en clair (n'importe quelle longueur).
        rounds: coût bcrypt (12 par défaut, ≥ 10 recommandé OWASP).

    Returns:
        Le hash bcrypt sous forme de string (`$2b$...`), prêt pour stockage BDD.

    Raises:
        ValueError: si le mot de passe est vide.
    """
    if not password:
        raise ValueError("Le mot de passe ne peut pas être vide.")
    if rounds < 4 or rounds > 31:
        raise ValueError("Le coût bcrypt doit être entre 4 et 31.")

    prepared = _prepare_password(password)
    salt = bcrypt.gensalt(rounds=rounds)
    hashed = bcrypt.hashpw(prepared, salt)
    return hashed.decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Vérifie qu'un mot de passe correspond à son hash bcrypt.

    Args:
        password: mot de passe en clair fourni par l'utilisateur.
        hashed: hash stocké en BDD.

    Returns:
        True si le mot de passe correspond, False sinon.
        Renvoie False (jamais une exception) en cas de hash malformé,
        pour ne pas leak d'information côté API ni faire crasher l'auth
        sur une donnée corrompue en BDD.
    """
    if not password or not hashed:
        return False

    # Validation préalable du format : la lib bcrypt panique au niveau Rust
    # sur les hashs malformés (panic non rattrapable par `except Exception`).
    if not _is_valid_bcrypt_hash(hashed):
        return False

    try:
        prepared = _prepare_password(password)
        return bcrypt.checkpw(prepared, hashed.encode("utf-8"))
    except Exception:  # noqa: BLE001 — défense en profondeur
        return False


def needs_rehash(hashed: str, target_rounds: int = DEFAULT_BCRYPT_ROUNDS) -> bool:
    """Indique si un hash doit être recalculé (rounds inférieurs à la cible).

    Utile pour faire évoluer le coût dans le temps : à chaque login réussi,
    on peut détecter les hashs anciens et les regénérer.
    """
    try:
        # Format bcrypt : $2b$<rounds>$<salt+hash>
        parts = hashed.split("$")
        if len(parts) < 4:
            return True
        current_rounds = int(parts[2])
        return current_rounds < target_rounds
    except (ValueError, IndexError):
        return True
