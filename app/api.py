"""Block 5 — FastAPI endpoint. Run: uvicorn app.api:app --reload"""
from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from app.generate import answer
from app.timeline import build_timeline
from app.timeline_parse import parse_situation, situation_to_dict
from app.timeline_evidence import attach_evidence
from app.reminders import send_reminders

app = FastAPI(title="OPT Navigator API")


class Q(BaseModel):
    question: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/ask")
def ask(q: Q) -> dict:
    text, hits = answer(q.question)
    return {"answer": text, "sources": [h["metadata"] for h in hits]}


class TimelineQ(BaseModel):
    situation: str


@app.post("/timeline")
def timeline(q: TimelineQ) -> dict:
    """Parse the student's situation (LLM) -> compute dates deterministically -> cited items."""
    s = parse_situation(q.situation)
    items = attach_evidence(build_timeline(s))
    return {
        "parsed": situation_to_dict(s),
        "timeline": [it.to_dict() for it in items],
    }


class RemindQ(BaseModel):
    situation: str
    email: str


@app.post("/remind")
def remind(q: RemindQ) -> dict:
    """Parse -> compute timeline -> email the upcoming deadlines (via Resend)."""
    s = parse_situation(q.situation)
    items = [it.to_dict() for it in attach_evidence(build_timeline(s))]
    return send_reminders(items, q.email)
