"""Exceptions métier de l'application.

Toutes les exceptions héritent de `AppException` et exposent un code stable,
un titre et un statut HTTP — conformes à RFC 7807 (Problem Details).
"""
from __future__ import annotations


class AppException(Exception):
    """Exception métier de base."""

    code: str = "app_error"
    title: str = "Erreur applicative"
    status_code: int = 500

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.title
        super().__init__(self.detail)


class NotFoundError(AppException):
    code = "not_found"
    title = "Ressource introuvable"
    status_code = 404


class ValidationError(AppException):
    code = "validation_error"
    title = "Données invalides"
    status_code = 422


class UnauthorizedError(AppException):
    code = "unauthorized"
    title = "Authentification requise"
    status_code = 401


class ForbiddenError(AppException):
    code = "forbidden"
    title = "Accès refusé"
    status_code = 403


class ConflictError(AppException):
    code = "conflict"
    title = "Conflit avec l'état actuel"
    status_code = 409


class RateLimitError(AppException):
    code = "rate_limit"
    title = "Limite de requêtes atteinte"
    status_code = 429


class ExternalServiceError(AppException):
    code = "external_service_error"
    title = "Service externe indisponible"
    status_code = 502
