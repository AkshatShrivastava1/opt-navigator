"""Deterministic OPT timeline + risk engine (Week 3 differentiator).

Given a student's situation (program end date, EAD dates, STEM-or-not,
unemployment days used), this computes their personal OPT dates and risk flags.

DESIGN RULE: the date math here is 100% deterministic Python. The LLM never
computes or invents a date — its only job (in a separate layer) is to parse a
student's free-text description into the `Situation` fields below, and RAG cites
the official rule behind each computed date. Every item carries its source URL.

Pure standard-library (datetime, calendar, dataclasses) so it is trivially
unit-testable and has no runtime dependencies.
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass, field
from datetime import date, timedelta

# --- Official sources for the rule behind each computed date -----------------
OPT_F1 = (
    "https://www.uscis.gov/working-in-the-united-states/students-and-exchange-"
    "visitors/optional-practical-training-opt-for-f-1-students"
)
STEM = (
    "https://www.uscis.gov/working-in-the-united-states/students-and-exchange-"
    "visitors/optional-practical-training-extension-for-stem-students-stem-opt"
)
POLICY_MANUAL_CH5 = "https://www.uscis.gov/policy-manual/volume-2-part-f-chapter-5"


def add_months(d: date, months: int) -> date:
    """Add whole months to a date, clamping the day to the target month's length.

    e.g. add_months(2025-01-31, 1) -> 2025-02-28 (2024 -> 2024-02-29).
    """
    m0 = d.month - 1 + months
    year = d.year + m0 // 12
    month = m0 % 12 + 1
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(d.day, last_day))


@dataclass
class Situation:
    """What we know about the student. Everything optional — compute what we can."""

    program_end_date: date | None = None
    is_stem: bool = False
    dso_recommendation_date: date | None = None
    ead_start_date: date | None = None
    ead_end_date: date | None = None
    unemployment_days_used: int | None = None
    on_stem_extension: bool = False    # currently ON the 24-month STEM extension (drives the 150-day limit)
    today: date = field(default_factory=date.today)


@dataclass
class TimelineItem:
    key: str
    label: str
    on_date: date | None          # the computed date, if this item is date-based
    value: str                    # human-readable value (ISO date or e.g. "10 days")
    rule: str                     # plain-English official rule
    citation: str                 # source URL for that rule
    status: str = "info"          # info | warning | danger
    detail: str = ""

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "label": self.label,
            "date": self.on_date.isoformat() if self.on_date else None,
            "value": self.value,
            "rule": self.rule,
            "citation": self.citation,
            "status": self.status,
            "detail": self.detail,
        }


def _opt_end(s: Situation) -> date | None:
    """EAD expiry: given ead_end, else 12 months from ead_start (post-completion OPT)."""
    if s.ead_end_date:
        return s.ead_end_date
    if s.ead_start_date:
        return add_months(s.ead_start_date, 12) - timedelta(days=1)
    return None


def build_timeline(s: Situation) -> list[TimelineItem]:
    """Compute every OPT date we have enough input for. Missing input -> skip (never guess)."""
    items: list[TimelineItem] = []

    # 1) Post-completion OPT application window --------------------------------
    if s.program_end_date:
        earliest = s.program_end_date - timedelta(days=90)
        latest = s.program_end_date + timedelta(days=60)
        items.append(TimelineItem(
            "apply_earliest",
            "Earliest you can file Form I-765 for post-completion OPT",
            earliest, earliest.isoformat(),
            "You may apply up to 90 days before your program end date.",
            OPT_F1,
        ))
        # Deadline, with a live risk flag based on today.
        if s.today > latest:
            status, detail = "danger", "This filing window has already closed."
        elif (latest - s.today).days <= 30:
            status, detail = "warning", f"Window closes in {(latest - s.today).days} days."
        else:
            status, detail = "info", ""
        items.append(TimelineItem(
            "apply_latest",
            "Latest you can file post-completion OPT",
            latest, latest.isoformat(),
            "You must apply no later than 60 days after your program end date.",
            OPT_F1, status=status, detail=detail,
        ))

    # File within 30 days of the DSO's SEVIS recommendation.
    if s.dso_recommendation_date:
        due = s.dso_recommendation_date + timedelta(days=30)
        items.append(TimelineItem(
            "file_within_30",
            "Deadline to file within 30 days of DSO recommendation",
            due, due.isoformat(),
            "USCIS must receive your Form I-765 within 30 days of your DSO entering "
            "the OPT recommendation in SEVIS, or it will be denied.",
            OPT_F1,
        ))

    # 2) EAD / OPT employment period ------------------------------------------
    if s.ead_start_date:
        items.append(TimelineItem(
            "work_start",
            "Earliest you may begin working",
            s.ead_start_date, s.ead_start_date.isoformat(),
            "You may not begin OPT employment until the start date on your EAD.",
            POLICY_MANUAL_CH5,
        ))
    opt_end = _opt_end(s)
    if opt_end:
        items.append(TimelineItem(
            "opt_end",
            "Post-completion OPT end date (EAD expiry)",
            opt_end, opt_end.isoformat(),
            "Post-completion OPT is granted for up to 12 months.",
            POLICY_MANUAL_CH5,
        ))
        grace_end = opt_end + timedelta(days=60)
        items.append(TimelineItem(
            "grace_end",
            "End of your 60-day grace period",
            grace_end, grace_end.isoformat(),
            "After OPT ends you have a 60-day grace period to depart the U.S., "
            "change status, or transfer to another SEVP-certified school.",
            POLICY_MANUAL_CH5,
        ))

    # 3) Unemployment limit + risk flag ---------------------------------------
    limit = 150 if s.on_stem_extension else 90
    limit_rule = (
        "You may accrue at most 150 days of unemployment in total across post-completion "
        "OPT and the STEM extension." if s.on_stem_extension else
        "You may accrue at most 90 days of unemployment during post-completion OPT. "
        "(The total allowance rises to 150 days only once you are on the STEM extension.)"
    )
    if s.unemployment_days_used is not None:
        remaining = limit - s.unemployment_days_used
        if remaining <= 0:
            status = "danger"
        elif remaining <= 15:
            status = "warning"
        else:
            status = "info"
        items.append(TimelineItem(
            "unemployment_remaining",
            f"Unemployment days remaining (limit {limit})",
            None, f"{max(remaining, 0)} days",
            limit_rule, STEM if s.on_stem_extension else POLICY_MANUAL_CH5,
            status=status,
            detail=f"{s.unemployment_days_used} of {limit} days used.",
        ))
    else:
        items.append(TimelineItem(
            "unemployment_limit",
            "Total unemployment allowance",
            None, f"{limit} days",
            limit_rule, STEM if s.on_stem_extension else POLICY_MANUAL_CH5,
        ))

    # 4) STEM OPT extension window (only if STEM-eligible and not yet on the extension) --
    if s.is_stem and not s.on_stem_extension and opt_end:
        stem_earliest = opt_end - timedelta(days=90)
        items.append(TimelineItem(
            "stem_apply_earliest",
            "Earliest to file the STEM OPT extension",
            stem_earliest, stem_earliest.isoformat(),
            "File the STEM extension up to 90 days before your current OPT EAD expires.",
            STEM,
        ))
        stem_end = add_months(opt_end, 24)
        items.append(TimelineItem(
            "stem_end",
            "Projected STEM OPT extension end date",
            stem_end, stem_end.isoformat(),
            "If you receive the STEM extension, it adds 24 months (projected from your "
            "current OPT end date).",
            STEM,
        ))

    return items


if __name__ == "__main__":
    demo = Situation(
        program_end_date=date(2026, 5, 15),
        dso_recommendation_date=date(2026, 5, 20),
        ead_start_date=date(2026, 7, 1),
        ead_end_date=date(2027, 6, 30),
        is_stem=False,
        unemployment_days_used=80,
        today=date(2026, 6, 1),
    )
    for it in build_timeline(demo):
        flag = {"info": "  ", "warning": "! ", "danger": "!!"}[it.status]
        print(f"{flag} {it.label}: {it.value}  [{it.citation.split('/')[-1][:40]}]")
        if it.detail:
            print(f"     {it.detail}")
