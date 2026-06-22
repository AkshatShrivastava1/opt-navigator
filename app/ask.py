"""Block 4 — quick CLI to test the cited-answer chain end to end.

Usage:
    python -m app.ask "How many unemployment days do I get on post-completion OPT?"

Prints the model's answer (which should cite [source: <url>] per claim, refuse
when the sources don't cover it, and end with the not-legal-advice line),
followed by the source chunks that were actually retrieved.
"""
from __future__ import annotations

import sys

from app.generate import answer


def main() -> None:
    if len(sys.argv) < 2:
        print('Usage: python -m app.ask "your question"')
        raise SystemExit(1)

    question = " ".join(sys.argv[1:])
    text, hits = answer(question)

    print(text)
    print("\n--- retrieved sources ---")
    seen: set[str] = set()
    for h in hits:
        src = h["metadata"].get("source", "?")
        if src in seen:
            continue
        seen.add(src)
        sim = round(h.get("similarity", 0), 3)
        print(f"  [{sim}] {h['metadata'].get('title', src)}\n        {src}")


if __name__ == "__main__":
    main()
