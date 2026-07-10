"""LLM situation parser for the timeline engine.

This is the ONLY place the LLM touches the timeline flow, and only to EXTRACT
the student's explicitly-stated facts into structured fields. It never computes,
estimates, or infers a date — all math happens in app.timeline.build_timeline.
"""
from __future__ import annotations

import json
from datetime import date

from app.config import settings
from app.generate import client  # reuse the (optionally Langfuse-traced) OpenAI client
from app.timeline import Situation

PARSE_SYSTEM = """You extract OPT facts from a student's message into JSON.

Return ONLY a JSON object with these keys, using null when the student did not
state it. NEVER guess, infer, or calculate a value:
- program_end_date: "YYYY-MM-DD" or null   (I-20 program end / graduation date)
- is_stem: true or false                    (true if they have a STEM degree / are STEM-eligible)
- on_stem_extension: true or false          (true ONLY if they say they are currently on, or already approved for, the 24-month STEM OPT extension; a STEM degree alone is NOT enough)
- dso_recommendation_date: "YYYY-MM-DD" or null
- ead_start_date: "YYYY-MM-DD" or null      (EAD / work-permit start date)
- ead_end_date: "YYYY-MM-DD" or null        (EAD / work-permit end date)
- unemployment_days_used: integer or null

Only extract what is explicitly stated. Do not calculate any date yourself."""


def _safe_date(v) -> date | None:
    try:
        return date.fromisoformat(v) if v else None
    except (ValueError, TypeError):
        return None


def _safe_int(v) -> int | None:
    try:
        return int(v) if v is not None else None
    except (ValueError, TypeError):
        return None


def parse_situation(text: str, today: date | None = None) -> Situation:
    resp = client.chat.completions.create(
        model=settings.CHAT_MODEL,
        messages=[
            {"role": "system", "content": PARSE_SYSTEM},
            {"role": "user", "content": text},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )
    data = json.loads(resp.choices[0].message.content)
    return Situation(
        program_end_date=_safe_date(data.get("program_end_date")),
        is_stem=bool(data.get("is_stem")),
        on_stem_extension=bool(data.get("on_stem_extension")),
        dso_recommendation_date=_safe_date(data.get("dso_recommendation_date")),
        ead_start_date=_safe_date(data.get("ead_start_date")),
        ead_end_date=_safe_date(data.get("ead_end_date")),
        unemployment_days_used=_safe_int(data.get("unemployment_days_used")),
        today=today or date.today(),
    )


def situation_to_dict(s: Situation) -> dict:
    """Echo the parsed fields back to the user for transparency (catch mis-parses)."""
    return {
        "program_end_date": s.program_end_date.isoformat() if s.program_end_date else None,
        "is_stem": s.is_stem,
        "on_stem_extension": s.on_stem_extension,
        "dso_recommendation_date": (
            s.dso_recommendation_date.isoformat() if s.dso_recommendation_date else None
        ),
        "ead_start_date": s.ead_start_date.isoformat() if s.ead_start_date else None,
        "ead_end_date": s.ead_end_date.isoformat() if s.ead_end_date else None,
        "unemployment_days_used": s.unemployment_days_used,
    }
