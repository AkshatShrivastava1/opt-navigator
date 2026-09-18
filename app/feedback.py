"""Week 14 — persist user feedback (thumbs up/down + optional comment) on an answer.

Why a table (not a log file): the app runs on an ephemeral container (Render), so a
local file wouldn't survive a restart. Feedback goes to Supabase, the same durable store
as the corpus, so it can later drive eval/corpus improvements — this is the on-demand →
persistent ("stateless → stateful") step for the product.

Mirrors reminders.py: pure-ish orchestration that returns a STATUS DICT and never raises,
so the API stays a clean 200 even when the write is misconfigured or fails.
"""
from __future__ import annotations

from supabase import create_client

from app.config import settings

# Module-level client singleton (built once, reused) — same pattern as retrieve.py.
_sb = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

VALID_RATINGS = {"up", "down"}


def save_feedback(
    question: str,
    answer: str,
    rating: str,
    comment: str | None = None,
    sources: list[dict] | None = None,
) -> dict:
    """Insert one feedback row. Returns {"saved": bool, ...}; never raises."""
    if rating not in VALID_RATINGS:
        return {"saved": False, "reason": f"rating must be one of {sorted(VALID_RATINGS)}"}
    row = {
        "question": (question or "")[:2000],
        "answer": (answer or "")[:8000],
        "rating": rating,
        "comment": (comment or None) and comment[:2000],
        "sources": sources or [],
    }
    try:
        _sb.table("feedback").insert(row).execute()
    except Exception as e:  # noqa: BLE001
        return {"saved": False, "reason": f"Couldn't save feedback: {str(e)[:120]}"}
    return {"saved": True}
