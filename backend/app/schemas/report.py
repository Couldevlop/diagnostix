"""Schémas Pydantic pour les rapports."""
from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel


class RiskOut(BaseModel):
    id: str
    title: str
    severity: str
    fcfa_impact: int


class RecommendationOut(BaseModel):
    priority: int
    title: str
    description: str
    expected_gain_fcfa: int
    implementation_weeks: int
    nexusrh_module: str


class ReportOut(BaseModel):
    report_id: uuid.UUID
    status: str
    global_score: float | None = None
    maturity_level: str | None = None
    scores_by_category: dict[str, float] | None = None
    risk_score: float | None = None
    financial_exposure_fcfa: int | None = None
    turnover_risk_proba: float | None = None
    digital_gap_pct: float | None = None
    executive_summary: str | None = None
    risks_detected: list[RiskOut] | None = None
    recommendations: list[RecommendationOut] | None = None
    pdf_url: str | None = None
    generated_at: Any = None


class AuthTokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
