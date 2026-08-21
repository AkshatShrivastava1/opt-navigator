"""Offline tests for the RAGAS-style metrics.

No network: a fake client returns canned JSON / embeddings so we can assert the
scoring MATH (which is the part we own) independently of the LLM judge.
"""
from __future__ import annotations

import json
from types import SimpleNamespace

from app.eval import ragas_metrics as rm


# --- fakes -----------------------------------------------------------------

class _FakeChat:
    def __init__(self, payload: dict):
        self._payload = payload

    def create(self, **kwargs):
        content = json.dumps(self._payload)
        msg = SimpleNamespace(content=content)
        return SimpleNamespace(choices=[SimpleNamespace(message=msg)])


class _FakeEmb:
    def __init__(self, table: dict[str, list[float]]):
        self._table = table

    def create(self, model, input):  # noqa: A002 - mirror the OpenAI signature
        return SimpleNamespace(data=[SimpleNamespace(embedding=self._table[t]) for t in input])


class FakeClient:
    def __init__(self, chat_payload: dict, emb_table: dict | None = None):
        self.chat = SimpleNamespace(completions=_FakeChat(chat_payload))
        self.embeddings = _FakeEmb(emb_table or {})


# --- strip_boilerplate -----------------------------------------------------

def test_strip_boilerplate_removes_citations_and_disclaimer():
    raw = (
        "You may not begin OPT until the start date on your EAD [source: https://x]. "
        "This is general information from official sources, not legal advice. Confirm "
        "your specific situation with your school's DSO or an immigration attorney."
    )
    out = rm.strip_boilerplate(raw)
    assert "[source:" not in out
    assert "not legal advice" not in out.lower()
    assert "begin OPT until the start date" in out


# --- faithfulness ----------------------------------------------------------

def test_faithfulness_fraction():
    payload = {"claims": [
        {"claim": "a", "supported": True},
        {"claim": "b", "supported": False},
        {"claim": "c", "supported": True},
    ]}
    res = rm.faithfulness("answer", ["ctx"], FakeClient(payload), "m")
    assert res["n_claims"] == 3
    assert res["n_supported"] == 2
    assert abs(res["score"] - 2 / 3) < 1e-9


def test_faithfulness_no_claims_scores_one():
    res = rm.faithfulness("answer", ["ctx"], FakeClient({"claims": []}), "m")
    assert res["score"] == 1.0
    assert res["n_claims"] == 0


# --- answer relevance ------------------------------------------------------

def test_answer_relevance_mean_cosine():
    payload = {"questions": ["q1", "q2"]}
    emb = {"real?": [1.0, 0.0], "q1": [1.0, 0.0], "q2": [0.0, 1.0]}  # cos 1 and 0 -> mean .5
    res = rm.answer_relevance("real?", "answer", FakeClient(payload, emb), "m")
    assert abs(res["score"] - 0.5) < 1e-9
    assert res["generated_questions"] == ["q1", "q2"]


def test_answer_relevance_no_questions_scores_zero():
    res = rm.answer_relevance("real?", "answer", FakeClient({"questions": []}), "m")
    assert res["score"] == 0.0


# --- context precision (order-aware) --------------------------------------

def test_context_precision_rewards_high_rank():
    # verdicts [T, F, T]: prec@1 = 1/1, prec@3 = 2/3; mean over 2 relevant = 0.8333
    payload = {"verdicts": [True, False, True]}
    res = rm.context_precision("q", "gt", ["c1", "c2", "c3"], FakeClient(payload), "m")
    assert abs(res["score"] - (1.0 + 2 / 3) / 2) < 1e-9


def test_context_precision_penalizes_low_rank():
    # verdicts [F, T]: only prec@2 = 1/2 counts; one relevant -> 0.5
    payload = {"verdicts": [False, True]}
    res = rm.context_precision("q", "gt", ["c1", "c2"], FakeClient(payload), "m")
    assert abs(res["score"] - 0.5) < 1e-9


def test_context_precision_pads_short_verdicts():
    # judge returned 1 verdict for 3 chunks -> padded to [T, F, F]; score 1.0
    payload = {"verdicts": [True]}
    res = rm.context_precision("q", "gt", ["c1", "c2", "c3"], FakeClient(payload), "m")
    assert res["verdicts"] == [True, False, False]
    assert res["score"] == 1.0


def test_context_precision_no_relevant_scores_zero():
    payload = {"verdicts": [False, False]}
    res = rm.context_precision("q", "gt", ["c1", "c2"], FakeClient(payload), "m")
    assert res["score"] == 0.0
