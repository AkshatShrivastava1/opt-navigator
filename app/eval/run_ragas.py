"""Week 10 — score the golden set with RAGAS-style metrics.

Usage:
    python -m app.eval.run_ragas            # all answerable questions
    python -m app.eval.run_ragas --limit 5  # quick smoke run

For every answerable golden question this runs the real pipeline (answer + its
retrieved chunks) and then scores three things with an LLM judge: faithfulness,
answer relevance, and context precision (see app/eval/ragas_metrics.py). It writes
a reviewable report to app/eval/ragas_results.md.

Refusal rows (expect_refusal=true) are skipped: RAGAS assumes there is a real
answer with a ground truth to score against, which a correct refusal has not. The
Week 1 guard eval (run_eval.py) already covers whether those refuse correctly.
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import date
from pathlib import Path

from app.config import settings
from app.generate import answer, client
from app.eval import ragas_metrics as rm

HERE = Path(__file__).parent
GOLDEN = HERE / "golden.jsonl"
OUT = HERE / "ragas_results.md"


def _fmt(x: float) -> str:
    return f"{x:.2f}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="score only the first N answerable rows")
    args = ap.parse_args()

    rows = [json.loads(line) for line in GOLDEN.read_text().splitlines() if line.strip()]
    answerable = [r for r in rows if not r.get("expect_refusal", False)]
    if args.limit:
        answerable = answerable[: args.limit]

    model = settings.CHAT_MODEL
    table = [
        "| # | question | faithful | relevance | ctx precision |",
        "|---|----------|:--------:|:---------:|:-------------:|",
    ]
    detail = []
    sums = {"faithfulness": 0.0, "answer_relevance": 0.0, "context_precision": 0.0}

    for i, row in enumerate(answerable, 1):
        q = row["q"]
        gt = row["expected"]
        text, hits = answer(q)
        contexts = [h["content"] for h in hits]

        f = rm.faithfulness(text, contexts, client, model)
        r = rm.answer_relevance(q, text, client, model)
        c = rm.context_precision(q, gt, contexts, client, model)

        sums["faithfulness"] += f["score"]
        sums["answer_relevance"] += r["score"]
        sums["context_precision"] += c["score"]

        table.append(
            f"| {i} | {q} | {_fmt(f['score'])} | {_fmt(r['score'])} | {_fmt(c['score'])} |"
        )
        unsupported = [c_["claim"] for c_ in f["claims"] if not c_.get("supported")]
        detail.append(
            f"### Q{i}. {q}\n\n"
            f"- **faithfulness** {_fmt(f['score'])} ({f['n_supported']}/{f['n_claims']} claims supported)\n"
            + (f"  - unsupported: {unsupported}\n" if unsupported else "")
            + f"- **answer relevance** {_fmt(r['score'])} — generated Qs: {r['generated_questions']}\n"
            f"- **context precision** {_fmt(c['score'])} — chunk verdicts: {c['verdicts']}\n"
        )
        print(
            f"Q{i:>2}: faithful={_fmt(f['score'])} "
            f"relevance={_fmt(r['score'])} ctx_prec={_fmt(c['score'])}"
        )

        # Cohere trial keys are capped ~10 calls/min; answer() reranks, so pace the loop.
        if settings.COHERE_API_KEY and i < len(answerable):
            time.sleep(7)

    n = len(answerable)
    avg = {k: (v / n if n else 0.0) for k, v in sums.items()}
    summary = (
        f"# RAGAS-style eval — {date.today().isoformat()}\n\n"
        f"Scored **{n}** answerable questions (refusal rows excluded; the guard eval "
        f"covers those). LLM judge: `{model}`, temperature 0.\n\n"
        f"| metric | mean |\n|---|:---:|\n"
        f"| faithfulness (grounding) | **{_fmt(avg['faithfulness'])}** |\n"
        f"| answer relevance | **{_fmt(avg['answer_relevance'])}** |\n"
        f"| context precision | **{_fmt(avg['context_precision'])}** |\n\n"
    )

    OUT.write_text(summary + "\n".join(table) + "\n\n---\n\n" + "\n".join(detail))
    print(
        f"\nMeans — faithful {_fmt(avg['faithfulness'])}, "
        f"relevance {_fmt(avg['answer_relevance'])}, "
        f"ctx_prec {_fmt(avg['context_precision'])}"
    )
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
