"""Cached "evidence" for the timeline: the verbatim official snippet behind each rule.

Why cached, not retrieved per request: the timeline cites a small, FIXED set of rules,
so we retrieve each rule's supporting passage ONCE (offline) and store it in
`timeline_evidence.json`, which the API just reads. Fixed inputs -> precompute, don't
recompute on every request. Keeps /timeline fast and off the reranker's rate limit.

Regenerate whenever the corpus changes (needs API keys + a live DB):
    python -m app.timeline_evidence      # writes app/timeline_evidence.json
"""
from __future__ import annotations

import json
import re
from pathlib import Path

EVIDENCE_PATH = Path(__file__).with_name("timeline_evidence.json")

# One retrieval query per distinct rule the timeline cites.
RULE_QUERIES = {
    "apply_window": "When can I apply for post-completion OPT relative to my program end date?",
    "file_within_30": "How soon must I file Form I-765 after my DSO recommends OPT in SEVIS?",
    "work_start": "Can I start working before my EAD start date?",
    "grace_period": "How long is the grace period after my OPT ends?",
    "unemployment": "How many days of unemployment am I allowed on post-completion OPT and STEM OPT?",
    "stem_window": "When can I file the STEM OPT extension?",
    "stem_duration": "How long is the STEM OPT extension?",
}

# Which rule each timeline item draws its evidence from.
ITEM_TO_RULE = {
    "apply_earliest": "apply_window",
    "apply_latest": "apply_window",
    "file_within_30": "file_within_30",
    "work_start": "work_start",
    "opt_end": "opt_duration",
    "grace_end": "grace_period",
    "unemployment_remaining": "unemployment",
    "unemployment_limit": "unemployment",
    "stem_apply_earliest": "stem_window",
    "stem_end": "stem_duration",
}

# Retrieval doesn't reliably surface the crispest passage for a couple of fixed rules,
# so we pin a human-curated verbatim quote (from the corpus) for those.
RULE_OVERRIDES = {
    "opt_duration": {
        "snippet": (
            "Eligible students can apply to receive up to 12 months of OPT employment "
            "authorization before completing their academic studies (pre-completion) and/or "
            "after completing their academic studies (post-completion)."
        ),
        "source": (
            "https://www.uscis.gov/working-in-the-united-states/students-and-exchange-"
            "visitors/optional-practical-training-opt-for-f-1-students"
        ),
        "title": "USCIS — Optional Practical Training (OPT) for F-1 Students",
    },
}

_MAX = 320  # snippet length cap


def _clean(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text[:_MAX] + ("…" if len(text) > _MAX else "")


def build_evidence() -> dict:
    """Retrieve the top supporting snippet for each rule and cache it to JSON."""
    from app.retrieve import retrieve  # imported here so the module loads without keys

    evidence: dict = {}
    for rule, query in RULE_QUERIES.items():
        hits = retrieve(query, k=1)
        if not hits:
            continue
        top = hits[0]
        evidence[rule] = {
            "snippet": _clean(top["content"]),
            "source": top["metadata"].get("source", ""),
            "title": top["metadata"].get("title", ""),
        }
        print(f"  {rule}: {evidence[rule]['title']}")
    for rule, ev in RULE_OVERRIDES.items():          # pin curated quotes where retrieval underperforms
        evidence[rule] = ev
        print(f"  {rule}: (curated) {ev['title']}")
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2))
    print(f"\nWrote {len(evidence)} rules to {EVIDENCE_PATH}")
    return evidence


def load_evidence() -> dict:
    try:
        return json.loads(EVIDENCE_PATH.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def attach_evidence(items):
    """Attach the cached official snippet to each timeline item (no-op if not generated yet)."""
    evidence = load_evidence()
    for it in items:
        ev = evidence.get(ITEM_TO_RULE.get(it.key, ""))
        if ev:
            it.snippet = ev["snippet"]
    return items


if __name__ == "__main__":
    build_evidence()
