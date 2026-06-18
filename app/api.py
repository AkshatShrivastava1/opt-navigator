"""Block 5 — FastAPI endpoint. Run: uvicorn app.api:app --reload"""
from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from app.generate import answer

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
