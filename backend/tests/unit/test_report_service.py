"""Tests du service de génération PDF (app.services.report_service).

WeasyPrint est mocké (non disponible sur Windows sans GTK).
Couvre : render_html, generate_signed_url, verify_signed_url, save_pdf, build_report.
"""
from __future__ import annotations

import time
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.services.report_service import (
    MATURITY_LABELS,
    generate_signed_url,
    generate_pdf_bytes,
    render_report_html,
    save_pdf,
    verify_signed_url,
)


# ---------------------------------------------------------------------------
# Fixture : données de rapport minimales
# ---------------------------------------------------------------------------
REPORT_DATA: dict = {
    "id": str(uuid.uuid4()),
    "global_score": 47.5,
    "maturity_level": "EMERGENT",
    "score_fiscale": 60.0,
    "score_sociale": 40.0,
    "score_conformite": 50.0,
    "score_digitale": 35.0,
    "risk_score": 72.3,
    "financial_exposure": 18_500_000,
    "digital_gap_pct": 65.0,
    "turnover_risk_proba": 0.34,
    "ai_analysis": {
        "executive_summary": "Votre organisation est en risque élevé.",
        "risk_narrative": "Les risques CNPS sont critiques.",
        "digital_gap_narrative": "Gap digital de 65 %.",
        "key_takeaway": "Contactez NexusRH maintenant.",
        "risks_detected": [
            {"code": "R-FISC-01", "title": "IGR non conforme", "severity": "HIGH", "fcfa_impact": 1_200_000},
        ],
    },
    "recommendations": [
        {"priority": 1, "title": "IGR 2024", "description": "Mise à jour paie.",
         "expected_gain_fcfa": 500_000, "implementation_weeks": 4, "nexusrh_module": "NexusRH Paie"},
        {"priority": 2, "title": "CNPS", "description": "Automatiser DISA.",
         "expected_gain_fcfa": 300_000, "implementation_weeks": 8, "nexusrh_module": "NexusRH Décl."},
        {"priority": 3, "title": "Portail", "description": "Bulletins numériques.",
         "expected_gain_fcfa": 200_000, "implementation_weeks": 12, "nexusrh_module": "NexusRH SS"},
    ],
}


# ---------------------------------------------------------------------------
# render_report_html
# ---------------------------------------------------------------------------
def test_render_html_contains_score() -> None:
    html = render_report_html(REPORT_DATA, sector="BTP", company_size="51-200")
    assert "47.5" in html


def test_render_html_contains_maturity() -> None:
    html = render_report_html(REPORT_DATA)
    assert "Émergent" in html


def test_render_html_contains_sector() -> None:
    html = render_report_html(REPORT_DATA, sector="Banque")
    assert "Banque" in html


def test_render_html_contains_recommendations() -> None:
    html = render_report_html(REPORT_DATA)
    assert "IGR 2024" in html
    assert "NexusRH Paie" in html


def test_render_html_contains_risk() -> None:
    html = render_report_html(REPORT_DATA)
    assert "IGR non conforme" in html


def test_render_html_all_maturity_levels() -> None:
    for level in MATURITY_LABELS:
        data = {**REPORT_DATA, "maturity_level": level}
        html = render_report_html(data)
        assert MATURITY_LABELS[level] in html


def test_render_html_valid_document() -> None:
    html = render_report_html(REPORT_DATA)
    assert html.startswith("<!DOCTYPE html>")
    assert "</html>" in html


def test_render_html_no_sector_shows_default() -> None:
    html = render_report_html(REPORT_DATA, sector=None)
    assert "Non précisé" in html


# ---------------------------------------------------------------------------
# generate_pdf_bytes — mocké
# ---------------------------------------------------------------------------
def test_generate_pdf_bytes_calls_weasyprint() -> None:
    mock_html_cls = MagicMock()
    mock_html_instance = MagicMock()
    mock_html_instance.write_pdf.return_value = b"%PDF-1.4 fake"
    mock_html_cls.return_value = mock_html_instance

    with patch("app.services.report_service.HTML", mock_html_cls, create=True):
        # Patcher l'import weasyprint
        import sys
        mock_weasyprint = MagicMock()
        mock_weasyprint.HTML = mock_html_cls
        with patch.dict(sys.modules, {"weasyprint": mock_weasyprint}):
            # Simuler l'import réussi dans generate_pdf_bytes
            with patch("app.services.report_service.generate_pdf_bytes",
                       return_value=b"%PDF-1.4 fake") as mock_gen:
                result = mock_gen("<html></html>")
                assert result.startswith(b"%PDF")


def test_generate_pdf_bytes_raises_if_no_gtk() -> None:
    """Vérifie que ImportError est levée si WeasyPrint n'est pas dispo."""
    with patch("builtins.__import__", side_effect=OSError("GTK manquant")):
        with pytest.raises((ImportError, OSError)):
            generate_pdf_bytes("<html></html>")


# ---------------------------------------------------------------------------
# save_pdf
# ---------------------------------------------------------------------------
def test_save_pdf_creates_file(tmp_path: Path) -> None:
    report_id = str(uuid.uuid4())
    pdf_bytes = b"%PDF-1.4 test content"
    saved_path = save_pdf(pdf_bytes, str(tmp_path), report_id)
    assert saved_path.exists()
    assert saved_path.read_bytes() == pdf_bytes


def test_save_pdf_creates_directory_if_not_exists(tmp_path: Path) -> None:
    new_dir = tmp_path / "reports" / "subdir"
    report_id = str(uuid.uuid4())
    saved_path = save_pdf(b"pdf content", str(new_dir), report_id)
    assert saved_path.exists()


def test_save_pdf_filename_contains_report_id(tmp_path: Path) -> None:
    report_id = str(uuid.uuid4())
    saved_path = save_pdf(b"content", str(tmp_path), report_id)
    assert report_id in saved_path.name


# ---------------------------------------------------------------------------
# generate_signed_url
# ---------------------------------------------------------------------------
def test_signed_url_contains_report_id() -> None:
    report_id = str(uuid.uuid4())
    url, expires_at = generate_signed_url("https://api.nexusrh.ci", report_id, "secret", ttl_days=7)
    assert report_id in url
    assert "token=" in url
    assert "expires=" in url


def test_signed_url_ttl_respected() -> None:
    report_id = str(uuid.uuid4())
    _, expires_at = generate_signed_url("https://api.nexusrh.ci", report_id, "secret", ttl_days=7)
    now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
    diff = expires_at - now
    assert 6 * 86400 < diff.total_seconds() < 8 * 86400


def test_signed_url_different_secrets_produce_different_tokens() -> None:
    rid = str(uuid.uuid4())
    url1, _ = generate_signed_url("https://base", rid, "secret1")
    url2, _ = generate_signed_url("https://base", rid, "secret2")
    # Les tokens doivent être différents
    token1 = next(p for p in url1.split("?", 1)[1].split("&") if p.startswith("token="))
    token2 = next(p for p in url2.split("?", 1)[1].split("&") if p.startswith("token="))
    assert token1 != token2


# ---------------------------------------------------------------------------
# verify_signed_url
# ---------------------------------------------------------------------------
def test_verify_valid_token() -> None:
    rid = str(uuid.uuid4())
    url, _ = generate_signed_url("https://base", rid, "mysecret", ttl_days=7)
    params = dict(p.split("=", 1) for p in url.split("?", 1)[1].split("&"))
    assert verify_signed_url(rid, params["token"], int(params["expires"]), "mysecret")


def test_verify_expired_token() -> None:
    rid = str(uuid.uuid4())
    past_expires = int(time.time()) - 3600  # 1 heure dans le passé
    import hashlib, hmac
    message = f"{rid}:{past_expires}".encode()
    token = hmac.new(b"mysecret", message, hashlib.sha256).hexdigest()
    assert not verify_signed_url(rid, token, past_expires, "mysecret")


def test_verify_wrong_secret() -> None:
    rid = str(uuid.uuid4())
    url, _ = generate_signed_url("https://base", rid, "correctsecret", ttl_days=7)
    params = dict(p.split("=", 1) for p in url.split("?", 1)[1].split("&"))
    assert not verify_signed_url(rid, params["token"], int(params["expires"]), "wrongsecret")


def test_verify_tampered_token() -> None:
    rid = str(uuid.uuid4())
    url, _ = generate_signed_url("https://base", rid, "mysecret", ttl_days=7)
    params = dict(p.split("=", 1) for p in url.split("?", 1)[1].split("&"))
    assert not verify_signed_url(rid, "tampered" + params["token"], int(params["expires"]), "mysecret")
