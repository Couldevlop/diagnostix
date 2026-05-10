"""Agrégateur des routeurs de l'API v1."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import admin, auth, questionnaire, reports, responses

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(questionnaire.router, prefix="/sessions", tags=["questionnaire"])
api_router.include_router(responses.router, prefix="/sessions", tags=["responses"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
