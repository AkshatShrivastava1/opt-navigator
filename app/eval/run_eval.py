"""Block 6 - run the golden set through the pipeline and record a baseline.

Usage:
    python -m app.eval.run_eval

Auto-checks the mechanical guards (a [source:] citation is present, the
not-legal-advice line is present, and out-of-scope questions are correctly
refused) and writes a reviewable table to app/eval/eval_results.md. You still
eyeball factual correctness and fill the 'correct?' column - that number is your
Week 1 baseline accuracy.
"""
from __future__ import annotations

import json
import time
from datetime import date
from pathlib import Path

from app.config import settings
from app.generate import answer

HERE = Path(__file__).parent
GOLDEN = HERE / "golden.jsonl"
OUT = HERE / "eval_results.md"

REFUSAL = "i don't have that in my official sources"
DISCLAIMER = "not legal advice"


def main() -> None:
    rows = [json.loads(line) for line in GOLDEN.read_text().splitlines() if line.strip()]

    table = [
        "| # | question | cited | disclaimer | refusal ok | correct? |",
        "|---|----------|:-----:|:----------:|:----------:|:--------:|",
    ]
    detail = []
    cited_n = disc_n = refusal_ok_n = 0

    for i, row in enumerate(rows, 1):
        q = row["q"]
        expect_refusal = bool(row.get("expect_refusal", False))
        text, hits = answer(q)
        low = text.lower()

        refused = REFUSAL in low
        cited = "[source:" in text
        disclaimer = DISCLAIMER in low
        cited_ok = cited or (expect_refusal and refused)   # refusals don't need a citation
        refusal_ok = refused == expect_refusal

        cited_n += cited_ok
        disc_n += disclaimer
        refusal_ok_n += refusal_ok

        mark = lambda b: "✅" if b else "❌"  # noqa: E731
        table.append(f"| {i} | {q} | {mark(cited_ok)} | {mark(disclaimer)} | {mark(refusal_ok)} |  |")
        detail.append(
            f"### Q{i}. {q}\n\n{text}\n\n"
            f"_retrieved:_ " + ", ".join(h["metadata"].get("source", "?") for h in hits) + "\n"
        )
        print(f"Q{i:>2}: cited={cited_ok}  disclaimer={disclaimer}  refusal_ok={refusal_ok}")

        # Cohere trial keys are capped at 10 calls/min; pace the eval so every question gets reranked.
        if settings.COHERE_API_KEY and i < len(rows):
            time.sleep(7)

    n = len(rows)
    summary = (
        f"# Eval baseline - {date.today().isoformat()}\n\n"
        f"- Questions: **{n}**\n"
        f"- Citation present (or correct refusal): **{cited_n}/{n}**\n"
        f"- Not-legal-advice line present: **{disc_n}/{n}**\n"
        f"- Refusal correct (refuses iff out-of-scope): **{refusal_ok_n}/{n}**\n\n"
        f"> These are automatic guard checks. Eyeball factual correctness in the "
        f"'correct?' column, then record that % as your Week 1 baseline.\n\n"
    )

    OUT.write_text(summary + "\n".join(table) + "\n\n---\n\n" + "\n".join(detail))
    print(f"\nGuards: cited {cited_n}/{n}, disclaimer {disc_n}/{n}, refusal {refusal_ok_n}/{n}")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
