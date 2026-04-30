"""Gmail SMTP notifier. Renders a Jinja2 HTML digest and sends via smtplib."""
from __future__ import annotations

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Iterable

from jinja2 import Environment, FileSystemLoader, select_autoescape

from radar.models import JobPost

log = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).parent / "templates"


def _render_html(jobs: list[JobPost]) -> str:
    """Render the job digest HTML from Jinja2 template."""
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("digest.html")
    return template.render(jobs=jobs, count=len(jobs))


def _send_email(subject: str, html_body: str, dry_run: bool = True) -> None:
    """Send HTML email via Gmail SMTP."""
    gmail_user = os.environ.get("GMAIL_USER", "")
    gmail_pass = os.environ.get("GMAIL_APP_PASSWORD", "")
    to_email = os.environ.get("NOTIFY_EMAIL", gmail_user)

    if not gmail_user or not gmail_pass:
        raise RuntimeError("GMAIL_USER / GMAIL_APP_PASSWORD env vars not set")

    if dry_run:
        log.info("[DRY RUN] Would send email to %s: %s", to_email, subject)
        log.info("HTML length: %d chars", len(html_body))
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = gmail_user
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
        server.starttls()
        server.login(gmail_user, gmail_pass)
        server.sendmail(gmail_user, [to_email], msg.as_string())

    log.info("Email sent to %s", to_email)


def send_digest(jobs: list[JobPost], dry_run: bool = True) -> None:
    """Build and send the job digest email. Skip send in dry-run mode."""
    if not jobs:
        log.info("No jobs to send — skipping email")
        return

    html = _render_html(jobs)
    subject = f"Job Radar: {len(jobs)} new roles matched your profile"
    _send_email(subject, html, dry_run=dry_run)