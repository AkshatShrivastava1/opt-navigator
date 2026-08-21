"""RAGAS-style evaluation metrics (Week 10).

Where the Week 1 eval only checked *mechanical* guards (is a [source:] citation
present, is the disclaimer present, did an out-of-scope question get refused),
these three metrics score *semantic* answer quality with an LLM as the judge —
the same idea the RAGAS framework formalizes:

  - faithfulness      : of the factual claims in the answer, what fraction are
                        actually supported by the retrieved context?  (grounding
                        / anti-hallucination signal)
  - answer_relevance  : does the answer actually address the question, or does it
                        wander?  (RAGAS trick: generate questions FROM the answer,
                        then measure how close they are to the real question.)
  - context_precision : were the *relevant* chunks ranked near the top of what we
                        retrieved?  (a retrieval-quality signal, order-aware.)

Design notes (kept deliberately small and testable):
  - The OpenAI client and the model name are INJECTED, never imported here. That
    keeps the judges free of network coupling and lets the unit test feed a fake
    client and assert the scoring math with no API calls.
  - Every judge runs at temperature 0 and asks for a strict JSON object, so the
    output is parseable and (as much as an LLM allows) reproducible.
  - All scores are in [0, 1]; higher is better.
"""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field


# --- small helpers ---------------------------------------------------------

_CITATION = re.compile(r"\[source:[^\]]*\]")
_DISCLAIMER = re.compile(
    r"this is general information.*?attorney\.?", re.IGNORECASE | re.DOTALL
)


def strip_boilerplate(answer: str) -> str:
    """Remove [source: ...] tags and the fixed not-legal-advice line.

    Those are template boilerplate present in *every* answer; leaving them in
    would pollute the claim decomposition and the answer-relevance embeddings.
    """
    text = _CITATION.sub("", answer)
    text = _DISCLAIMER.sub("", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _judge_json(client, model: str, system: str, user: str) -> dict:
    """One temperature-0 chat call constrained to a JSON object; parsed to a dict."""
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content)


# --- metric 1: faithfulness ------------------------------------------------

_FAITHFULNESS_SYS = (
    "You are a strict fact-checker. You are given an ANSWER and the CONTEXT it was "
    "supposedly written from. Break the ANSWER into atomic factual claims (ignore "
    "hedging, greetings, and advice to consult a DSO/attorney). For EACH claim decide "
    "whether it can be directly inferred from the CONTEXT. Judge only against the "
    "CONTEXT, never outside knowledge. Reply as JSON: "
    '{"claims": [{"claim": "<text>", "supported": true|false}]}.'
)


def faithfulness(answer: str, contexts: list[str], client, model: str) -> dict:
    """Fraction of the answer's atomic claims that the context supports.

    Returns {"score", "n_claims", "n_supported", "claims"}. An answer with no
    checkable factual claims (e.g. a pure refusal) scores 1.0 — there is nothing
    unfaithful in it — but n_claims=0 lets the runner treat it specially if wanted.
    """
    body = strip_boilerplate(answer)
    context_blob = "\n\n---\n\n".join(contexts)
    data = _judge_json(
        client,
        model,
        _FAITHFULNESS_SYS,
        f"CONTEXT:\n{context_blob}\n\nANSWER:\n{body}",
    )
    claims = data.get("claims", [])
    n = len(claims)
    supported = sum(1 for c in claims if c.get("supported"))
    score = 1.0 if n == 0 else supported / n
    return {"score": score, "n_claims": n, "n_supported": supported, "claims": claims}


# --- metric 2: answer relevance -------------------------------------------

_RELEVANCE_SYS = (
    "Given an ANSWER, generate the questions that this answer would most directly and "
    "completely answer. Produce exactly {n} distinct, self-contained questions. "
    'Reply as JSON: {"questions": ["...", "..."]}.'
)


def answer_relevance(
    question: str, answer: str, client, model: str, n_gen: int = 3
) -> dict:
    """How on-topic the answer is, via RAGAS's reverse-question trick.

    Ask the LLM to reconstruct the questions the answer addresses, embed them and
    the real question, and average the cosine similarity. A focused, on-point
    answer reconstructs questions close to the original; a rambling or evasive one
    does not. Returns {"score", "generated_questions"}.
    """
    body = strip_boilerplate(answer)
    data = _judge_json(
        client,
        model,
        _RELEVANCE_SYS.replace("{n}", str(n_gen)),
        f"ANSWER:\n{body}",
    )
    gen = [q for q in data.get("questions", []) if q.strip()]
    if not gen:
        return {"score": 0.0, "generated_questions": []}

    texts = [question] + gen
    emb = client.embeddings.create(model="text-embedding-3-small", input=texts)
    vecs = [d.embedding for d in emb.data]
    q_vec, gen_vecs = vecs[0], vecs[1:]
    sims = [_cosine(q_vec, g) for g in gen_vecs]
    return {"score": sum(sims) / len(sims), "generated_questions": gen}


# --- metric 3: context precision ------------------------------------------

_CTX_PRECISION_SYS = (
    "You are judging retrieval quality. Given a QUESTION, a reference GROUND_TRUTH "
    "answer, and an ordered list of retrieved CONTEXT chunks, decide for EACH chunk "
    "whether it is useful for producing the ground-truth answer. "
    'Reply as JSON: {"verdicts": [true|false, ...]} in the SAME order as the chunks.'
)


def context_precision(
    question: str, ground_truth: str, contexts: list[str], client, model: str
) -> dict:
    """Order-aware precision of the retrieved chunks (RAGAS context precision@k).

    score = sum_k ( precision@k * relevant_k ) / (total relevant)
    so relevant chunks ranked HIGH are rewarded and relevant chunks buried low are
    penalized. Returns {"score", "verdicts"}.
    """
    if not contexts:
        return {"score": 0.0, "verdicts": []}
    numbered = "\n\n".join(f"[{i}] {c}" for i, c in enumerate(contexts))
    data = _judge_json(
        client,
        model,
        _CTX_PRECISION_SYS,
        f"QUESTION:\n{question}\n\nGROUND_TRUTH:\n{ground_truth}\n\nCONTEXT:\n{numbered}",
    )
    verdicts = [bool(v) for v in data.get("verdicts", [])]
    # pad/truncate to the number of chunks so the math never index-errors
    verdicts = (verdicts + [False] * len(contexts))[: len(contexts)]

    total_relevant = sum(verdicts)
    if total_relevant == 0:
        return {"score": 0.0, "verdicts": verdicts}

    running_hits = 0
    weighted = 0.0
    for k, rel in enumerate(verdicts, start=1):
        if rel:
            running_hits += 1
            precision_at_k = running_hits / k
            weighted += precision_at_k
    return {"score": weighted / total_relevant, "verdicts": verdicts}


# --- convenience container -------------------------------------------------

@dataclass
class Scores:
    faithfulness: float = 0.0
    answer_relevance: float = 0.0
    context_precision: float = 0.0
    n_claims: int = 0
    detail: dict = field(default_factory=dict)

    def mean(self) -> float:
        return (self.faithfulness + self.answer_relevance + self.context_precision) / 3
