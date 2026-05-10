"""Service d'envoi d'emails (Sprint 8).

Supporte deux backends :
- SMTP via aiosmtplib (développement / staging)
- SendGrid API (production, activé si SENDGRID_API_KEY est défini)

Le template HTML est embarqué dans ce module (pas de fichier externe)
pour simplifier le déploiement.
"""
from __future__ import annotations

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

logger = logging.getLogger("app.email_service")

# ---------------------------------------------------------------------------
# Template HTML responsive (inline — conforme ARTCI)
# ---------------------------------------------------------------------------
_REPORT_EMAIL_HTML = """\
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Votre rapport Nexus-Diagnostix</title>
</head>
<body style="margin:0;padding:0;background:#F4F4F5;font-family:Inter,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#F4F4F5;padding:32px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0"
             style="background:#0A0A0A;border-radius:12px 12px 0 0;overflow:hidden;">
        <tr>
          <td style="padding:32px 40px;">
            <span style="font-size:22pt;font-weight:700;color:#FF5A1F;
                         font-family:Georgia,serif;">NexusRH</span>
          </td>
        </tr>
        <tr>
          <td style="padding:0 40px 32px;color:#FFFFFF;">
            <h1 style="font-size:20pt;margin:0 0 8px;">Votre rapport Nexus-Diagnostix est prêt</h1>
            <p style="color:#9CA3AF;margin:0;">Diagnostic de maturité digitale RH</p>
          </td>
        </tr>
      </table>

      <table width="600" cellpadding="0" cellspacing="0"
             style="background:#FFFFFF;border-radius:0 0 12px 12px;overflow:hidden;">
        <tr>
          <td style="padding:40px;">
            <p style="font-size:11pt;color:#374151;line-height:1.6;margin:0 0 20px;">
              Bonjour,
            </p>
            <p style="font-size:11pt;color:#374151;line-height:1.6;margin:0 0 20px;">
              Votre rapport de diagnostic de maturité digitale RH a été généré avec succès.
              Il contient :
            </p>
            <ul style="font-size:11pt;color:#374151;line-height:1.8;margin:0 0 24px;padding-left:20px;">
              <li>Votre <strong>score global : {global_score}/100</strong>
                  (niveau <strong>{maturity_level_label}</strong>)</li>
              <li>L'analyse détaillée de vos risques fiscaux et sociaux</li>
              <li>Votre gap digital par rapport au standard IA-Native</li>
              <li>3 recommandations stratégiques prioritaires</li>
            </ul>

            <table cellpadding="0" cellspacing="0" style="margin:0 0 32px;">
              <tr>
                <td style="background:#FF5A1F;border-radius:8px;padding:14px 32px;">
                  <a href="{pdf_url}"
                     style="color:#FFFFFF;text-decoration:none;font-size:12pt;font-weight:700;">
                    📥 Télécharger mon rapport PDF
                  </a>
                </td>
              </tr>
            </table>

            <p style="font-size:9pt;color:#9CA3AF;margin:0 0 8px;">
              Ce lien est valable <strong>7 jours</strong>.
            </p>

            <hr style="border:none;border-top:1px solid #E5E7EB;margin:24px 0;">

            <p style="font-size:9pt;color:#9CA3AF;line-height:1.5;margin:0;">
              Conformément à la Loi n°2013-450 relative à la protection des données personnelles,
              vous pouvez demander la suppression de vos données à tout moment en nous contactant à
              <a href="mailto:dpo@openlabconsulting.com" style="color:#FF5A1F;">
                dpo@openlabconsulting.com</a>.<br>
              © 2026 OpenLab Consulting — NexusRH CI. Tous droits réservés.
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""

_REPORT_EMAIL_PLAIN = """\
Votre rapport Nexus-Diagnostix est prêt

Score global : {global_score}/100 — Niveau : {maturity_level_label}

Téléchargez votre rapport (valable 7 jours) :
{pdf_url}

---
Conformément à la Loi n°2013-450 (ARTCI), vous pouvez demander la suppression
de vos données à : dpo@openlabconsulting.com
© 2026 OpenLab Consulting — NexusRH CI
"""


# ---------------------------------------------------------------------------
# Construction du message MIME
# ---------------------------------------------------------------------------
def build_report_message(
    to_email: str,
    from_email: str,
    global_score: float,
    maturity_level_label: str,
    pdf_url: str,
) -> MIMEMultipart:
    """Construit un MIMEMultipart text/html + text/plain."""
    ctx: dict[str, Any] = {
        "global_score": round(global_score, 1),
        "maturity_level_label": maturity_level_label,
        "pdf_url": pdf_url,
    }
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Votre rapport Nexus-Diagnostix — score {ctx['global_score']}/100"
    msg["From"] = from_email
    msg["To"] = to_email
    msg.attach(MIMEText(_REPORT_EMAIL_PLAIN.format(**ctx), "plain", "utf-8"))
    msg.attach(MIMEText(_REPORT_EMAIL_HTML.format(**ctx), "html", "utf-8"))
    return msg


# ---------------------------------------------------------------------------
# Backend SMTP (aiosmtplib)
# ---------------------------------------------------------------------------
async def send_via_smtp(
    msg: MIMEMultipart,
    host: str,
    port: int,
    username: str | None = None,
    password: str | None = None,
    use_tls: bool = True,
) -> None:
    """Envoie le message via SMTP asynchrone (aiosmtplib)."""
    try:
        import aiosmtplib
    except ImportError as exc:
        raise ImportError("aiosmtplib est requis pour l'envoi SMTP.") from exc

    # Port 587 = STARTTLS (upgrade plain→TLS), port 465 = SSL direct
    start_tls = port == 587
    actual_use_tls = use_tls and not start_tls

    await aiosmtplib.send(
        msg,
        hostname=host,
        port=port,
        username=username,
        password=password,
        use_tls=actual_use_tls,
        start_tls=start_tls,
    )
    logger.info("email_service.smtp_sent to=%s", msg["To"])


# ---------------------------------------------------------------------------
# Backend SendGrid
# ---------------------------------------------------------------------------
async def send_via_sendgrid(
    msg: MIMEMultipart,
    api_key: str,
) -> None:
    """Envoie le message via l'API SendGrid (python-http-client synchrone, wrappé)."""
    import asyncio

    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
    except ImportError as exc:
        raise ImportError("sendgrid est requis pour ce backend.") from exc

    mail = Mail(
        from_email=msg["From"],
        to_emails=msg["To"],
        subject=msg["Subject"],
    )
    mail.add_content(
        next(p.get_payload(decode=True).decode("utf-8") for p in msg.get_payload()
             if p.get_content_type() == "text/plain"),
        "text/plain",
    )
    mail.add_content(
        next(p.get_payload(decode=True).decode("utf-8") for p in msg.get_payload()
             if p.get_content_type() == "text/html"),
        "text/html",
    )

    sg = SendGridAPIClient(api_key)
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, lambda: sg.send(mail))
    logger.info("email_service.sendgrid_sent to=%s status=%s", msg["To"], response.status_code)


# ---------------------------------------------------------------------------
# Point d'entrée haut niveau
# ---------------------------------------------------------------------------
async def send_report_email(
    to_email: str,
    from_email: str,
    global_score: float,
    maturity_level_label: str,
    pdf_url: str,
    *,
    sendgrid_api_key: str | None = None,
    smtp_host: str = "localhost",
    smtp_port: int = 587,
    smtp_username: str | None = None,
    smtp_password: str | None = None,
    smtp_use_tls: bool = True,
) -> None:
    """Envoie le rapport par email.

    Utilise SendGrid si sendgrid_api_key est fourni, sinon SMTP.
    """
    msg = build_report_message(to_email, from_email, global_score, maturity_level_label, pdf_url)

    if sendgrid_api_key:
        await send_via_sendgrid(msg, sendgrid_api_key)
    else:
        await send_via_smtp(
            msg, smtp_host, smtp_port,
            username=smtp_username,
            password=smtp_password,
            use_tls=smtp_use_tls,
        )
