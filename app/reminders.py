"""Week 8 - email deadline reminders. The tool acts, not just answers.

Given a computed timeline, find the deadlines coming up within a window (or already
flagged as a risk) and email the student a summary via Resend (a real external email
API, key-authenticated). Graceful: if RESEND_API_KEY isn't set, sending is skipped
with a clear reason instead of erroring.
"""
from __future__ import annotations

from datetime import date, timedelta

import requests

from app.config import settings

RESEND_ENDPOINT = "https://api.resend.com/emails"


def upcoming_deadlines(items: list[dict], within_days: int = 45, today: date | None = None) -> list[dict]:
    """Timeline items that are either a date within the window, or already flagged as a risk."""
    today = today or date.today()
    horizon = today + timedelta(days=within_days)
    out: list[dict] = []
    for it in items:
        upcoming_date = False
        d = it.get("date")
        if d:
            try:
                upcoming_date = today <= date.fromisoformat(d) <= horizon
            except ValueError:
                pass
        if upcoming_date or it.get("status") in ("warning", "danger"):
            out.append(it)
    return out


def compose_email(deadlines: list[dict]) -> tuple[str, str]:
    """Return (subject, html) for the reminder email."""
    subject = f"Your OPT deadlines — {len(deadlines)} to watch"
    flags = {"info": "", "warning": "⚠️ ", "danger": "🚨 "}
    rows = []
    for it in deadlines:
        detail = f" — {it['detail']}" if it.get("detail") else ""
        rows.append(
            f"<li style='margin-bottom:10px'>{flags.get(it.get('status'), '')}"
            f"<b>{it['label']}: {it['value']}</b>{detail}"
            f"<br><span style='color:#555;font-size:13px'>{it['rule']} "
            f"<a href='{it['citation']}'>[source]</a></span></li>"
        )
    html = (
        "<div style='font-family:sans-serif;max-width:600px'>"
        "<h2>Your OPT deadlines</h2>"
        "<p>Here are the OPT dates coming up for you, each with the official rule:</p>"
        f"<ul style='padding-left:18px'>{''.join(rows)}</ul>"
        "<p style='color:#777;font-size:12px'>Computed from the details you provided. General "
        "information from official USCIS/SEVP sources, not legal advice — confirm with your DSO.</p>"
        "</div>"
    )
    return subject, html


def send_email(to: str, subject: str, html: str) -> dict:
    resp = requests.post(
        RESEND_ENDPOINT,
        headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}"},
        json={"from": settings.REMINDER_FROM, "to": [to], "subject": subject, "html": html},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def send_reminders(items: list[dict], email: str) -> dict:
    """Filter upcoming deadlines and email them. Returns a status summary (never raises)."""
    deadlines = upcoming_deadlines(items)
    if not deadlines:
        return {"sent": False, "count": 0, "reason": "No deadlines within the reminder window."}
    if not settings.RESEND_API_KEY:
        return {
            "sent": False,
            "count": len(deadlines),
            "reason": "Email isn't configured on the server (RESEND_API_KEY not set).",
        }
    subject, html = compose_email(deadlines)
    try:
        send_email(email, subject, html)
    except Exception as e:  # noqa: BLE001
        return {"sent": False, "count": len(deadlines), "reason": f"Send failed: {e}"}
    return {"sent": True, "count": len(deadlines), "deadlines": [it["label"] for it in deadlines]}
