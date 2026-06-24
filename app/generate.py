"""Block 4 — citation-enforced answer generation with high-stakes OPT guards.

Implemented later this week. The SYSTEM prompt below is the OPT-specific guard
set from Week1_Plan_OPT_Navigator.md. Keep temperature=0.
"""
from __future__ import annotations

from app.config import settings
from app.retrieve import retrieve


def _make_client():
    """Langfuse drop-in (auto-traces every call) when LANGFUSE keys are set; else plain OpenAI."""
    if settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY:
        try:
            from langfuse.openai import OpenAI  # traced drop-in replacement

            return OpenAI(api_key=settings.OPENAI_API_KEY)
        except Exception:
            pass
    from openai import OpenAI

    return OpenAI(api_key=settings.OPENAI_API_KEY)


client = _make_client()

SYSTEM = """You help F-1 students understand U.S. OPT rules using ONLY the official sources provided in context.

RULES:
- Answer ONLY from the provided sources. End EVERY factual sentence with a citation in the form [source: <url>]. In a bulleted or multi-part answer, put a [source: <url>] on EACH bullet. An answer that contains no [source: ...] citation is invalid: if you cannot cite it from the sources, you do not have it.
- If the answer is not clearly in the sources, reply exactly:
  "I don't have that in my official sources - please confirm with your DSO."
- Never invent or estimate dates, deadlines, day-counts, or eligibility decisions.
- Do not infer permissions the sources do not explicitly grant. Never state that a student may work, may begin working, or is authorized to do something unless a source explicitly says so for that exact situation. If the sources grant a status (e.g., "may remain in F-1 status") but say nothing about working, state only what is given and do not claim they may work.
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
