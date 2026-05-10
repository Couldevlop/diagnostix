"""Tests du service email (Sprint 8).

Couvre : build_report_message, send_via_smtp (mock aiosmtplib),
         send_report_email (routage SMTP / SendGrid).
"""
from __future__ import annotations

from email.mime.multipart import MIMEMultipart
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.email_service import (
    build_report_message,
    send_report_email,
    send_via_smtp,
)


# ---------------------------------------------------------------------------
# build_report_message
# ---------------------------------------------------------------------------
def test_build_message_returns_mime_multipart() -> None:
    msg = build_report_message(
        "drh@example.ci", "noreply@nexusrh.ci",
        47.5, "Émergent", "https://api.nexusrh.ci/reports/xxx/pdf?token=abc",
    )
    assert isinstance(msg, MIMEMultipart)


def test_build_message_subject_contains_score() -> None:
    msg = build_report_message(
        "drh@example.ci", "noreply@nexusrh.ci",
        73.0, "Structuré", "https://example.com/pdf",
    )
    assert "73.0" in msg["Subject"]


def test_build_message_to_and_from() -> None:
    msg = build_report_message(
        "dest@ci.ci", "sender@ci.ci", 50.0, "Structuré", "http://url"
    )
    assert msg["To"] == "dest@ci.ci"
    assert msg["From"] == "sender@ci.ci"


def test_build_message_has_plain_and_html_parts() -> None:
    msg = build_report_message(
        "a@b.ci", "c@d.ci", 60.0, "Optimisé", "http://pdf"
    )
    content_types = {p.get_content_type() for p in msg.get_payload()}
    assert "text/plain" in content_types
    assert "text/html" in content_types


def test_build_message_html_contains_score() -> None:
    msg = build_report_message(
        "a@b.ci", "c@d.ci", 92.5, "IA-Native", "http://pdf"
    )
    html_part = next(
        p.get_payload(decode=True).decode("utf-8")
        for p in msg.get_payload()
        if p.get_content_type() == "text/html"
    )
    assert "92.5" in html_part
    assert "IA-Native" in html_part
    assert "http://pdf" in html_part


def test_build_message_plain_contains_url() -> None:
    msg = build_report_message(
        "a@b.ci", "c@d.ci", 30.0, "Critique", "https://signed-url.ci"
    )
    plain_part = next(
        p.get_payload(decode=True).decode("utf-8")
        for p in msg.get_payload()
        if p.get_content_type() == "text/plain"
    )
    assert "https://signed-url.ci" in plain_part


def test_build_message_plain_contains_artci_mention() -> None:
    msg = build_report_message("a@b.ci", "c@d.ci", 50.0, "Émergent", "http://url")
    plain_part = next(
        p.get_payload(decode=True).decode("utf-8")
        for p in msg.get_payload()
        if p.get_content_type() == "text/plain"
    )
    assert "ARTCI" in plain_part or "2013-450" in plain_part


# ---------------------------------------------------------------------------
# send_via_smtp — mock aiosmtplib.send
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_send_via_smtp_calls_aiosmtplib() -> None:
    msg = build_report_message(
        "dest@ci.ci", "src@ci.ci", 50.0, "Structuré", "http://pdf"
    )
    mock_send = AsyncMock()
    mock_aiosmtplib = MagicMock()
    mock_aiosmtplib.send = mock_send

    with patch.dict("sys.modules", {"aiosmtplib": mock_aiosmtplib}):
        await send_via_smtp(msg, "smtp.example.com", 587, "user", "pass")

    mock_send.assert_awaited_once()
    call_kwargs = mock_send.call_args
    assert call_kwargs[1]["hostname"] == "smtp.example.com"
    assert call_kwargs[1]["port"] == 587


@pytest.mark.asyncio
async def test_send_via_smtp_raises_if_no_aiosmtplib() -> None:
    msg = build_report_message("a@b.ci", "c@d.ci", 50.0, "Émergent", "http://u")
    import sys
    saved = sys.modules.pop("aiosmtplib", None)
    try:
        with patch.dict("sys.modules", {"aiosmtplib": None}):
            with pytest.raises(ImportError):
                await send_via_smtp(msg, "localhost", 25, use_tls=False)
    finally:
        if saved is not None:
            sys.modules["aiosmtplib"] = saved


# ---------------------------------------------------------------------------
# send_report_email — routage
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_send_report_email_uses_smtp_when_no_sendgrid() -> None:
    smtp_mock = AsyncMock()
    with patch("app.services.email_service.send_via_smtp", smtp_mock):
        await send_report_email(
            "drh@example.ci", "noreply@nexusrh.ci",
            47.5, "Émergent", "https://pdf.url",
            smtp_host="mail.example.com", smtp_port=587,
        )
    smtp_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_report_email_uses_sendgrid_when_key_given() -> None:
    sg_mock = AsyncMock()
    with patch("app.services.email_service.send_via_sendgrid", sg_mock):
        await send_report_email(
            "drh@example.ci", "noreply@nexusrh.ci",
            47.5, "Émergent", "https://pdf.url",
            sendgrid_api_key="SG.fake-key",
        )
    sg_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_report_email_passes_correct_data() -> None:
    smtp_mock = AsyncMock()
    with patch("app.services.email_service.send_via_smtp", smtp_mock):
        await send_report_email(
            "drh@example.ci", "noreply@nexusrh.ci",
            73.0, "Structuré", "https://signed-url/pdf",
            smtp_host="localhost", smtp_port=1025, smtp_use_tls=False,
        )
    call_args = smtp_mock.call_args
    msg_arg = call_args[0][0]
    assert msg_arg["To"] == "drh@example.ci"
    assert "73.0" in msg_arg["Subject"]
