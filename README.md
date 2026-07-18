# OPT Navigator

**Cited answers and personalized deadlines for F-1 students on OPT — grounded only in official USCIS/SEVP sources.**

🔗 **Live demo:** https://opt-navigator-bcmpeyc9h48ebvdwrlh4wc.streamlit.app
🔗 **API (Swagger):** https://opt-navigator-api.onrender.com/docs

> ⚠️ Informational only, **not legal advice**. Every answer says so, and the assistant refuses rather than guesses. Always confirm with your DSO or an immigration attorney.

---

## Why this exists

OPT rules are scattered across a dozen USCIS/SEVP pages, and getting them wrong has real consequences — missed filing windows, blown unemployment limits, lost status. Generic AI chatbots confidently make things up, which is dangerous here. OPT Navigator does the opposite:

- **Answers only from official federal sources**, with a citation on every claim.
- **Refuses cleanly** ("I don't have that in my official sources — please confirm with your DSO") when the corpus doesn't cover it.
- **Computes your personal deadlines deterministically** — the LLM never does date math.

## What makes it more than a chatbot

The **personalized OPT timeline**: describe your situation in plain English and it computes *your* dates — filing window, earliest work date, OPT end, 60-day grace period, unemployment days remaining (the 90 vs 150 limit handled by OPT phase, not just degree), STEM extension window — each with a risk flag (🟢🟡🔴) and the official rule cited.

The design rule that makes this trustworthy: **the LLM only parses your text into fields.** All date arithmetic is plain, unit-tested Python (leap years, month-end clamping, phase-dependent limits). The parsed fields are echoed back so any misread is visible and correctable.

## Architecture

```
                 ┌── Q&A path ──────────────────────────────────────────────┐
 user question ─►│ hybrid retrieval (Postgres FTS + pgvector, RRF fusion)   │
                 │   └─► Cohere Rerank (top-20 → top-5, graceful fallback)  │
                 │        └─► LLM answer: cite every claim, else refuse     │
                 └──────────────────────────────────────────────────────────┘
                 ┌── Timeline path ─────────────────────────────────────────┐
 user situation ─►│ LLM parser (extract fields ONLY) ─► deterministic date  │
                 │  engine (pure Python, unit-tested) ─► cited dates + risk │
                 └──────────────────────────────────────────────────────────┘

 corpus: 9 official USCIS/DHS sources → 106 chunks in Supabase (pgvector + RLS)
 observability: Langfuse traces (latency, cost, prompts) on every request
```

**Stack:** Python · FastAPI · Streamlit · Supabase (Postgres + pgvector) · OpenAI (gpt-4o-mini, text-embedding-3-small) · Cohere Rerank · Langfuse · Docker · Render + Streamlit Community Cloud

## Evaluation (prove it with numbers)

Golden set of 16 real OPT questions, scored for correctness + valid citation + correct refusal:

| Stage | Score |
|-------|-------|
| Baseline (naive vector RAG) | 11/16 (~69%) |
| + anti-inference faithfulness rule | 12/16 (75%) |
| + hybrid retrieval (FTS + vector, RRF) | 12/16 (fixed a retrieval miss, exposed corpus gaps) |
| + Cohere reranking | 12/16 (precision infra; invisible to a binary metric) |
| **+ targeted corpus expansion** | **15/16 (~94%)** |

The one remaining "miss" is a **deliberate refusal**: no official source explicitly states the answer, so the assistant declines to assert it. In this domain, that restraint is the feature.

Full decision log — trade-offs, what broke and how it was fixed, and how this would scale to 10+ universities: **[ENGINEERING_DECISIONS.md](ENGINEERING_DECISIONS.md)**

## Run it locally

```bash
git clone https://github.com/AkshatShrivastava1/opt-navigator.git && cd opt-navigator
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # fill in: OpenAI, Supabase (Cohere/Langfuse optional)

# one-time: apply sql/001-003 in the Supabase SQL editor, then ingest the corpus
python -m app.ingest --reset

uvicorn app.api:app --reload            # API  -> http://localhost:8000/docs
streamlit run frontend/app.py           # UI   -> http://localhost:8501
python -m app.eval.run_eval             # eval -> app/eval/eval_results.md
```

Or with Docker:

```bash
docker build -t opt-navigator-api .
docker run -p 8000:8000 --env-file .env opt-navigator-api
```

## Repo map

```
app/            config, ingest, retrieve (hybrid+rerank), generate (guarded LLM),
                timeline (deterministic engine), timeline_parse, api, eval/
frontend/       Streamlit UI (Ask + My OPT timeline)
sql/            pgvector schema, match_documents, hybrid_search (RRF)
data/raw/       9 official source docs + sources.json provenance manifest
tests/          unit tests for the date engine (leap years, phase-dependent limits)
```

## Limitations (honest ones)

- **Federal sources only** — school-specific ISSS processes are a planned per-university layer.
- **Free-tier hosting** — first request after idle cold-starts (~30–60s); Supabase auto-pauses after 7 idle days (mitigated with a scheduled keep-alive).
- **The eval is small (16) and binary** — RAGAS-style faithfulness/context-precision metrics are the next measurement step.
- **Not legal advice.** It says so on every answer, on purpose.
