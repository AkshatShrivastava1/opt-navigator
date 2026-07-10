"""Unit tests for the deterministic OPT timeline engine (app/timeline.py).

Run: PYTHONPATH=. python tests/test_timeline.py    (or: pytest tests/)
Pure standard library — no network, no API keys, no LLM.
"""
from __future__ import annotations

from datetime import date

from app.timeline import Situation, add_months, build_timeline


def _by_key(items):
    return {it.key: it for it in items}


def test_add_months_clamps_and_rolls_over():
    assert add_months(date(2025, 1, 31), 1) == date(2025, 2, 28)   # non-leap clamp
    assert add_months(date(2024, 1, 31), 1) == date(2024, 2, 29)   # leap-year clamp
    assert add_months(date(2026, 12, 15), 1) == date(2027, 1, 15)  # year rollover
    assert add_months(date(2027, 6, 30), 24) == date(2029, 6, 30)  # STEM +24 months


def test_non_stem_full_situation():
    s = Situation(
        program_end_date=date(2026, 5, 15),
        dso_recommendation_date=date(2026, 5, 20),
        ead_start_date=date(2026, 7, 1),
        ead_end_date=date(2027, 6, 30),
        is_stem=False,
        unemployment_days_used=80,
        today=date(2026, 6, 1),
    )
    it = _by_key(build_timeline(s))
    assert it["apply_earliest"].on_date == date(2026, 2, 14)   # program end - 90
    assert it["apply_latest"].on_date == date(2026, 7, 14)     # program end + 60
    assert it["file_within_30"].on_date == date(2026, 6, 19)   # DSO rec + 30
    assert it["work_start"].on_date == date(2026, 7, 1)        # EAD start
    assert it["opt_end"].on_date == date(2027, 6, 30)          # EAD end
    assert it["grace_end"].on_date == date(2027, 8, 29)        # EAD end + 60
    assert it["unemployment_remaining"].value == "10 days"     # 90 - 80
    assert it["unemployment_remaining"].status == "warning"    # <= 15 left
    # every item must carry a citation
    assert all(i.citation.startswith("https://www.uscis.gov") for i in it.values())


def test_stem_eligible_but_on_initial_opt_uses_90_limit():
    # Has a STEM degree but is still on the INITIAL post-completion OPT -> the 90-day limit applies.
    s = Situation(
        ead_start_date=date(2026, 7, 1),
        ead_end_date=date(2027, 6, 30),
        is_stem=True,
        on_stem_extension=False,
        unemployment_days_used=80,
    )
    it = _by_key(build_timeline(s))
    assert it["unemployment_remaining"].value == "10 days"        # 90 - 80 (NOT 150 - 80)
    assert it["unemployment_remaining"].status == "warning"
    # Still eligible to file the STEM extension, so those items should show:
    assert it["stem_apply_earliest"].on_date == date(2027, 4, 1)  # EAD end - 90
    assert it["stem_end"].on_date == date(2029, 6, 30)            # EAD end + 24 months


def test_on_stem_extension_uses_150_limit():
    # Actually ON the STEM extension -> the 150-day total applies.
    s = Situation(
        ead_start_date=date(2026, 7, 1),
        ead_end_date=date(2027, 6, 30),
        is_stem=True,
        on_stem_extension=True,
        unemployment_days_used=140,
    )
    it = _by_key(build_timeline(s))
    assert it["unemployment_remaining"].value == "10 days"        # 150 - 140
    assert it["unemployment_remaining"].status == "warning"
    assert "stem_apply_earliest" not in it                        # already on it; nothing to file


def test_partial_input_only_program_end():
    s = Situation(program_end_date=date(2026, 5, 15))
    keys = {it.key for it in build_timeline(s)}
    assert "apply_earliest" in keys and "apply_latest" in keys
    assert "opt_end" not in keys and "file_within_30" not in keys  # no EAD / no DSO date
    assert "unemployment_limit" in keys                            # defaults to the 90-day allowance


def test_risk_flags():
    # Filing window already closed
    s = Situation(program_end_date=date(2026, 5, 15), today=date(2026, 8, 1))
    assert _by_key(build_timeline(s))["apply_latest"].status == "danger"
    # Unemployment limit exceeded -> clamps to 0 and flags danger
    s2 = Situation(is_stem=False, unemployment_days_used=95)
    rem = _by_key(build_timeline(s2))["unemployment_remaining"]
    assert rem.value == "0 days" and rem.status == "danger"


def _run_all():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"PASS  {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL  {t.__name__}: {e}")
    print(f"\n{passed}/{len(tests)} passed")
    return passed == len(tests)


if __name__ == "__main__":
    import sys

    sys.exit(0 if _run_all() else 1)
