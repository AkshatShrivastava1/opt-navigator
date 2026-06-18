"""Block 6 — run the golden set through the pipeline and record a baseline.

Usage: python -m app.eval.run_eval
Scores are eyeballed for Week 1 (correct + valid citation + correct refusal).
"""
from __future__ import annotations

import json
from pathlib import Path

from app.generate import answer

GOLDEN = Path(__file__).parent / "golden.jsonl"


def main() -> None:
    rows = [json.loads(line) for line in GOLDEN.read_text().splitlines() if line.strip()]
    for i, row in enumerate(rows, 1):
        text, hits = answer(row["q"])
        print(f"\n=== Q{i}: {row['q']}")
        print(f"expected: {row.get('expected', '')}")
        print(f"answer:   {text}")
        print(f"sources:  {[h['metadata'].get('source') for h in hits]}")


if __name__ == "__main__":
    main()
