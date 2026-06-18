"""Block 4 — citation-enforced answer generation with high-stakes OPT guards.

Implemented later this week. The SYSTEM prompt below is the OPT-specific guard
set from Week1_Plan_OPT_Navigator.md. Keep temperature=0.
"""
from __future__ import annotations

from openai import OpenAI

from app.config import settings
from app.retrieve import retrieve

client = OpenAI(api_key=settings.OPENAI_API_KEY)

SYSTEM = """You help F-1 students understand U.S. OPT rules using ONLY the official sources provided in context.

RULES:
- Answer ONLY from the provided sources. Cite every claim like [source: <url>].
- If the answer is not clearly in the sources, reply exactly:
  "I don't have that in my official sources - please confirm with your DSO."
- Never invent or estimate dates, deadlines, day-counts, or eligibility decisions.
- Define acronyms on first use (OPT, EAD, DSO, SEVIS, STEM).
- Always end every answer with this line:
  "This is general information from official sources, not legal advice. Confirm your specific situation with your school's DSO or an immigration attorney."
"""


def answer(query: str) -> tuple[str, list[dict]]:
    hits = retrieve(query)
    context = "\n\n".join(
        f"[source: {h['metadata'].get('source', '?')}]\n{h['content']}" for h in hits
    )
    resp = client.chat.completions.create(
        model=settings.CHAT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
        ],
        temperature=0,
    )
    return resp.choices[0].message.content, hits
