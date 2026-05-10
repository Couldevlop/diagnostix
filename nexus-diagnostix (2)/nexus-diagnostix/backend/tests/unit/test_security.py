"""Tests du module `app.core.security`.

Couvre le hashing bcrypt natif et notamment le **fix du bug rencontré en prod**
sur les mots de passe > 72 bytes, qui faisait crasher le seed avec :

    ValueError: password cannot be longer than 72 bytes, truncate manually
    if necessary (e.g. my_password[:72])
"""
from __future__ import annotations

import pytest

from app.core.security import (
    BCRYPT_MAX_PASSWORD_BYTES,
    DEFAULT_BCRYPT_ROUNDS,
    _prepare_password,
    hash_password,
    needs_rehash,
    verify_password,
)


# =============================================================================
# hash_password / verify_password — round-trip
# =============================================================================
class TestHashAndVerify:
    """Round-trip : un mot de passe hashé doit pouvoir être vérifié."""

    def test_hash_simple_password(self) -> None:
        h = hash_password("simple_password")
        assert h.startswith("$2b$")
        assert verify_password("simple_password", h) is True

    def test_hash_with_special_chars(self) -> None:
        """Mots de passe avec caractères spéciaux usuels."""
        password = "Admin@1234!"
        h = hash_password(password)
        assert verify_password(password, h) is True

    def test_hash_with_unicode(self) -> None:
        """Caractères non-ASCII (accents, emojis)."""
        password = "Mot_de_passe_éàç_中文_🔒"
        h = hash_password(password)
        assert verify_password(password, h) is True

    def test_wrong_password_returns_false(self) -> None:
        h = hash_password("correct")
        assert verify_password("wrong", h) is False

    def test_two_hashes_of_same_password_differ(self) -> None:
        """Le sel doit garantir des hashs différents pour le même mot de passe."""
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2
        # Mais les deux vérifient
        assert verify_password("same", h1) is True
        assert verify_password("same", h2) is True


# =============================================================================
# Bug 72 bytes — couverture explicite du cas qui crashait
# =============================================================================
class TestLongPasswordsHandling:
    """Le module DOIT gérer silencieusement les mots de passe > 72 bytes
    via un pré-hash SHA-256, conformément aux pratiques OWASP."""

    def test_password_exactly_72_bytes_works(self) -> None:
        """72 bytes = limite haute, pas de pré-hash nécessaire."""
        password = "a" * 72
        assert len(password.encode("utf-8")) == 72
        h = hash_password(password)
        assert verify_password(password, h) is True

    def test_password_73_bytes_uses_prehash(self) -> None:
        """73 bytes = au-dessus de la limite → pré-hash transparent."""
        password = "a" * 73
        h = hash_password(password)
        assert verify_password(password, h) is True

    def test_password_1000_bytes_works(self) -> None:
        """Le bug original : un long mot de passe ne doit PLUS crasher."""
        password = "x" * 1000
        # Avec passlib + bcrypt 4.x, cette ligne plantait avec
        # ValueError("password cannot be longer than 72 bytes")
        h = hash_password(password)
        assert verify_password(password, h) is True

    def test_long_password_unicode_works(self) -> None:
        """UTF-8 multi-byte : 200 caractères chinois = 600 bytes."""
        password = "中" * 200
        assert len(password.encode("utf-8")) == 600
        h = hash_password(password)
        assert verify_password(password, h) is True

    def test_two_different_long_passwords_have_different_hashes(self) -> None:
        """Le pré-hash SHA-256 doit préserver l'unicité."""
        p1 = "a" * 100
        p2 = "b" * 100
        h1 = hash_password(p1)
        h2 = hash_password(p2)
        assert h1 != h2
        assert verify_password(p1, h2) is False
        assert verify_password(p2, h1) is False


# =============================================================================
# _prepare_password — détail interne (pour la couverture 100 %)
# =============================================================================
class TestPreparePassword:
    def test_short_password_not_prehashed(self) -> None:
        """Mot de passe court → bytes UTF-8 directs."""
        result = _prepare_password("short")
        assert result == b"short"

    def test_long_password_is_prehashed(self) -> None:
        """Mot de passe long → SHA-256 base64 (44 bytes)."""
        password = "a" * 100
        result = _prepare_password(password)
        assert len(result) <= BCRYPT_MAX_PASSWORD_BYTES
        # La sortie SHA-256 base64 fait toujours 44 bytes
        assert len(result) == 44

    def test_prehash_is_deterministic(self) -> None:
        password = "x" * 200
        assert _prepare_password(password) == _prepare_password(password)


# =============================================================================
# Validations d'entrée
# =============================================================================
class TestInputValidation:
    def test_empty_password_raises(self) -> None:
        with pytest.raises(ValueError, match="vide"):
            hash_password("")

    def test_invalid_rounds_too_low(self) -> None:
        with pytest.raises(ValueError, match="entre 4 et 31"):
            hash_password("password", rounds=3)

    def test_invalid_rounds_too_high(self) -> None:
        with pytest.raises(ValueError, match="entre 4 et 31"):
            hash_password("password", rounds=32)

    def test_verify_with_empty_password_returns_false(self) -> None:
        h = hash_password("password")
        assert verify_password("", h) is False

    def test_verify_with_empty_hash_returns_false(self) -> None:
        assert verify_password("password", "") is False

    def test_verify_with_malformed_hash_returns_false(self) -> None:
        """Ne doit jamais lever d'exception, même sur hash corrompu."""
        assert verify_password("password", "not-a-valid-bcrypt-hash") is False

    def test_verify_with_truncated_hash_returns_false(self) -> None:
        assert verify_password("password", "$2b$12$tooshort") is False


# =============================================================================
# needs_rehash — politique d'évolution du coût bcrypt
# =============================================================================
class TestNeedsRehash:
    def test_current_hash_does_not_need_rehash(self) -> None:
        h = hash_password("password", rounds=DEFAULT_BCRYPT_ROUNDS)
        assert needs_rehash(h) is False

    def test_low_cost_hash_needs_rehash(self) -> None:
        h = hash_password("password", rounds=4)
        assert needs_rehash(h, target_rounds=DEFAULT_BCRYPT_ROUNDS) is True

    def test_higher_cost_hash_does_not_need_rehash(self) -> None:
        """Un hash plus cher que la cible n'a pas besoin de downgrade."""
        h = hash_password("password", rounds=14)
        assert needs_rehash(h, target_rounds=DEFAULT_BCRYPT_ROUNDS) is False

    def test_malformed_hash_needs_rehash(self) -> None:
        assert needs_rehash("not-a-valid-hash") is True

    def test_empty_hash_needs_rehash(self) -> None:
        assert needs_rehash("") is True

    def test_hash_with_invalid_rounds_needs_rehash(self) -> None:
        """Si on n'arrive pas à parser le coût, on rehash par sécurité."""
        assert needs_rehash("$2b$xx$malformed") is True


# =============================================================================
# Reproduction explicite du scénario de prod qui crashait
# =============================================================================
def test_reproduction_seed_admin_scenario() -> None:
    """Reproduit le scénario du seed initial qui crashait en prod.

    Contexte du bug :
        File seed_initial_data.py, line 271, in seed_admin
            password_hash=pwd_context.hash(plain_password)
        ValueError: password cannot be longer than 72 bytes

    Notre fix doit faire passer ce test silencieusement.
    """
    # Le seed génère un mot de passe de 16 caractères ASCII — ne devrait
    # JAMAIS dépasser 72 bytes. Le bug venait de passlib + bcrypt incompat.
    short_admin_password = "Aa1@" * 4  # 16 bytes
    h_short = hash_password(short_admin_password)
    assert verify_password(short_admin_password, h_short)

    # Mais même un mot de passe paranoïaque doit fonctionner
    long_paranoid_password = "MyAdmin@SuperSecure!Password#WithLotsOfSpecialChars$%^&*()_+1234567890" * 3
    assert len(long_paranoid_password.encode("utf-8")) > 72
    h_long = hash_password(long_paranoid_password)
    assert verify_password(long_paranoid_password, h_long)
