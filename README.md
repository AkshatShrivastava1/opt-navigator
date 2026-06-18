# OPT Navigator

A citation-only assistant that helps F-1 students understand U.S. OPT rules — grounded **only** in official USCIS / SEVP sources, with every claim cited. Built to be trustworthy in a high-stakes domain: it answers from the docs, says "I don't have that — confirm with your DSO" when unsure, and never gives legal advice.

> ⚠️ This tool provides general information from official sources. It is **not legal advice**. Always confirm your specific situation with your school's DSO or an immigration attorney.

## Why it exists
OPT rules are scattered across USCIS pages, the SEVP/DHS portal, and the Policy Manual, and getting them wrong has real consequences. This gives students fast, **cited** answers they can trace back to the source.

## Status
🚧 Building in public. Week 1 = cited Q&A MVP. Week 2 = personalized timeline + risk engine.

## Tech stack
Python · Supabase (pgvector) · OpenAI API · LangChain (light) · FastAPI · Streamlit · Langfuse · deployed on Render.

## Repo structure
```
rag-assistant/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── app/
│   ├── __init__.py
│   ├── config.py        # loads + validates env (done)
│   ├── ingest.py        # Block 2–3: load + chunk + embed + upsert
│   ├── retrieve.py      # Block 4: vector search (later: + BM25, rerank)
│   ├── generate.py      # Block 4: prompt + LLM + citations
│   ├── api.py           # Block 5: FastAPI endpoint
│   └── eval/
│       ├── golden.jsonl # Block 6: eval questions
│       └── run_eval.py
├── data/raw/            # source docs (gitignored)
└── frontend/
    └── app.py           # Block 5: Streamlit UI
```

## Quickstart
```bash
git clone <your-repo-url> && cd rag-assistant
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                 # then fill in your keys
python -c "from app.config import settings; settings.validate(); print('env OK')"
```
If that prints `env OK`, you're set up correctly.

## Source corpus (official, federal)
Saved to `data/raw/`. Citations point back to these:
1. USCIS — OPT for F-1 Students
2. USCIS — Students and Employment
3. USCIS — STEM OPT Extension
4. USCIS Policy Manual — Vol. 2, Part F, Ch. 5 (Practical Training)
5. USCIS — Cap-Gap
6. DHS Study in the States — F-1 OPT (SEVIS Help Hub) + SEVP Portal pages
7. Form I-765 instructions

(Full URLs in the OPT build plan doc.)

## Roadmap
- **Week 1** — Cited Q&A over the federal corpus, deployed, with guards + a 15-question eval set.
- **Week 2** — Hybrid retrieval (BM25 + vector) + reranking; personalized timeline + risk engine (deterministic date math, cited rules).
- **Week 3+** — Agent loop (retrieval + timeline + checklist tools), follow-up Q&A, per-university layer, first real users, Langfuse-driven iteration.

## Guardrails (non-negotiable)
- Answer only from retrieved official sources; cite every claim.
- Refuse cleanly when the answer isn't in the sources.
- Never invent dates, deadlines, or eligibility decisions.
- Always append the "not legal advice" line.
