"""Service de génération du rapport PDF (Sprint 7 — §10 du CLAUDE.md).

Pipeline :
1. Rendu du template Jinja2 HTML avec les données du rapport.
2. Conversion HTML → PDF via WeasyPrint.
3. Stockage local chiffré (path configurable via Settings).
4. Génération d'une URL signée HMAC-SHA256 (TTL 7 jours).
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger("app.report_service")

# Chemin du répertoire de templates
_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

MATURITY_LABELS: dict[str, str] = {
    "CRITIQUE":  "Critique",
    "EMERGENT":  "Émergent",
    "STRUCTURE": "Structuré",
    "OPTIMISE":  "Optimisé",
    "IA_NATIVE": "IA-Native",
}


# ---------------------------------------------------------------------------
# Rendu HTML
# ---------------------------------------------------------------------------
def render_report_html(
    report_data: dict[str, Any],
    sector: str | None = None,
    company_size: str | None = None,
) -> str:
    """Rend le template Jinja2 avec les données du rapport."""
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("report.html")

    ai = report_data.get("ai_analysis", {})
    recos = report_data.get("recommendations", [])

    context = {
        "report_id": str(report_data.get("id", uuid.uuid4())),
        "generated_at": datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC"),
        "sector": sector or "Non précisé",
        "company_size": company_size or "Non précisée",
        "global_score": float(report_data.get("global_score", 0)),
        "maturity_level_label": MATURITY_LABELS.get(
            report_data.get("maturity_level", "CRITIQUE"), "Critique"
        ),
        "scores_by_category": {
            "Fiscale": float(report_data.get("score_fiscale", 0)),
            "Sociale": float(report_data.get("score_sociale", 0)),
            "Conformité": float(report_data.get("score_conformite", 0)),
            "Digitale": float(report_data.get("score_digitale", 0)),
        },
        "risk_score": float(report_data.get("risk_score", 0)),
        "financial_exposure": int(report_data.get("financial_exposure", 0)),
        "digital_gap_pct": float(report_data.get("digital_gap_pct", 0)),
        "turnover_risk_proba": report_data.get("turnover_risk_proba"),
        "executive_summary": ai.get("executive_summary", ""),
        "risk_narrative": ai.get("risk_narrative", ""),
        "digital_gap_narrative": ai.get("digital_gap_narrative", ""),
        "key_takeaway": ai.get("key_takeaway", ""),
        "risks_detected": [
            {
                "code": r.get("code", ""),
                "title": r.get("title", ""),
                "severity": r.get("severity", "LOW"),
                "fcfa_impact": r.get("fcfa_impact", 0),
            }
            for r in (ai.get("risks_detected") or [])
        ],
        "recommendations": [
            {
                "priority": r.get("priority", 0),
                "title": r.get("title", ""),
                "description": r.get("description", ""),
                "expected_gain_fcfa": r.get("expected_gain_fcfa", 0),
                "implementation_weeks": r.get("implementation_weeks", 0),
                "nexusrh_module": r.get("nexusrh_module", ""),
            }
            for r in recos
        ],
    }
    return template.render(**context)


# ---------------------------------------------------------------------------
# Génération PDF
# ---------------------------------------------------------------------------
def generate_pdf_bytes(html: str) -> bytes:
    """Convertit le HTML en PDF via WeasyPrint.

    Raises:
        ImportError: si WeasyPrint ou ses dépendances système sont absentes
                     (GTK/Pango requis, disponibles dans Docker).
    """
    try:
        from weasyprint import HTML
        return HTML(string=html).write_pdf()  # type: ignore[no-untyped-call]
    except (ImportError, OSError) as exc:
        raise ImportError(
            "WeasyPrint nécessite GTK/Pango (disponible dans le container Docker). "
            f"Erreur d'origine : {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# Stockage
# ---------------------------------------------------------------------------
def save_pdf(pdf_bytes: bytes, storage_path: str, report_id: str | uuid.UUID) -> Path:
    """Écrit le PDF dans le répertoire de stockage et retourne son chemin."""
    base = Path(storage_path)
    base.mkdir(parents=True, exist_ok=True)
    path = base / f"{report_id}.pdf"
    path.write_bytes(pdf_bytes)
    logger.info("report_service.pdf_saved", extra={"path": str(path), "size": len(pdf_bytes)})
    return path


# ---------------------------------------------------------------------------
# URL signée
# ---------------------------------------------------------------------------
def generate_signed_url(
    base_url: str,
    report_id: str | uuid.UUID,
    signing_secret: str,
    ttl_days: int = 7,
) -> tuple[str, datetime]:
    """Génère une URL signée HMAC-SHA256 avec expiration.

    Returns:
        (url_signée, date_expiration)
    """
    expires_at = datetime.now(timezone.utc) + timedelta(days=ttl_days)
    expires_ts = int(expires_at.timestamp())
    message = f"{report_id}:{expires_ts}".encode()
    signature = hmac.new(
        signing_secret.encode(), message, hashlib.sha256
    ).hexdigest()
    url = f"{base_url}/api/v1/reports/{report_id}/pdf?token={signature}&expires={expires_ts}"
    return url, expires_at


def verify_signed_url(
    report_id: str | uuid.UUID,
    token: str,
    expires: int,
    signing_secret: str,
) -> bool:
    """Vérifie la validité du token signé (HMAC + TTL)."""
    if time.time() > expires:
        return False
    message = f"{report_id}:{expires}".encode()
    expected = hmac.new(signing_secret.encode(), message, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, token)


# ---------------------------------------------------------------------------
# Point d'entrée haut niveau
# ---------------------------------------------------------------------------
def build_report(
    report_data: dict[str, Any],
    storage_path: str,
    base_url: str,
    signing_secret: str,
    ttl_days: int = 7,
    sector: str | None = None,
    company_size: str | None = None,
) -> tuple[Path, str, datetime]:
    """Génère le PDF, le stocke, retourne (path, signed_url, expires_at)."""
    html = render_report_html(report_data, sector=sector, company_size=company_size)
    pdf_bytes = generate_pdf_bytes(html)
    pdf_path = save_pdf(pdf_bytes, storage_path, report_data.get("id", uuid.uuid4()))
    signed_url, expires_at = generate_signed_url(
        base_url, report_data["id"], signing_secret, ttl_days
    )
    return pdf_path, signed_url, expires_at
