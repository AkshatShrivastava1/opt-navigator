# Engineering Decisions — OPT Navigator

This document is the scoping, the trade-offs, and the failure log behind OPT Navigator.
It exists because in a high-stakes domain the *judgment* behind the system matters more
than the code. It is written the way a forward-deployed engineer would hand a project off.

---

## 1. Problem & scope

**Problem.** F-1 students on OPT have to get time-sensitive, status-affecting decisions right
(when to file, how many unemployment days they have left, when their grace period ends), and the
rules are scattered across a dozen USCIS/SEVP pages. Generic chatbots will confidently make an
answer up, which is dangerous here.

**Scope (deliberately narrow).**
- **In:** cited Q&A grounded *only* in official federal sources (USCIS + DHS/SEVP), and a
  personalized OPT date/risk engine.
- **Out (for now):** school-specific ISSS processes. Kept federal-first so the tool generalizes to
  every F-1 student; the per-university layer is a planned, clearly-labeled add-on (see §7).
- **Non-negotiables:** cite every claim; refuse cleanly when the answer isn't in the sources;
  never invent a date; always show the "not legal advice" line.

---

## 2. Architecture

```
                    ┌── Q&A path ─────────────────────────────────────────┐
  user question ──► hybrid retrieve (FTS + vector, RRF) ─► Cohere rerank ─► LLM answer (cite every claim / refuse)
                    │        (Supabase / pgvector, 106 chunks, 9 sources)  │
                    └─────────────────────────────────────────────────────┘

                    ┌── Timeline path ────────────────────────────────────┐
  user situation ─► LLM parser (EXTRACT fields only) ─► deterministic date engine ─► cited dates + risk flags
                    │                                    (pure Python, unit-tested)  │
                    └─────────────────────────────────────────────────────┘
```

**Stack:** Python · FastAPI · Streamlit · Supabase (Postgres + pgvector) · OpenAI
(`gpt-4o-mini`, `text-embedding-3-small`) · Cohere Rerank · Langfuse (tracing) · Render +
Streamlit Community Cloud.

---

## 3. Key decisions & trade-offs

**The LLM never does math or invents a date.** The timeline engine is 100% deterministic Python.
The LLM's only job on that path is to *parse* a student's free text into structured fields; every
date is then computed by tested code, and RAG supplies the official rule behind each date. This is
the single most important design choice — it's what makes a status-affecting tool trustworthy.

**Hybrid retrieval, and why the full-text arm is computed inline.** Pure vector search "smears
over" exact keywords (it missed a "volunteer/unpaid work" passage that was in the corpus). I added
a Postgres full-text arm and fused it with vector via Reciprocal Rank Fusion (RRF). I intentionally
compute `to_tsvector` **inline** rather than adding a stored `fts` column + GIN index: on Supabase's
free tier, adding the column triggers a table rewrite that rebuilds the ivfflat vector index, which
exceeds `maintenance_work_mem` (needs 61MB, cap is 32MB). Inline is instant at this corpus size;
the stored column + index is the right move once the corpus grows on a bigger tier.

**Full-text uses OR, not AND.** `websearch_to_tsquery` ANDs all terms, so a long question matched
nothing. I convert it to OR semantics so any salient term is a candidate; RRF + reranking supply
the precision.

**Reranking with a hosted API (Cohere), not a local model.** A local cross-encoder (~400MB + torch)
won't fit Render's free tier. Cohere Rerank is one authenticated API call, hosted, and degrades
gracefully. Trade-off: an external dependency and a trial-key rate limit (handled — see §4).

**Cite-every-claim + an anti-inference rule.** The prompt requires a `[source:]` on every sentence
and every bullet, and forbids asserting a permission the sources don't explicitly grant. Cost:
slightly more conservative (it will refuse a true-but-unstated fact — see Q7 in §5), which is the
correct trade in this domain.

**Graceful degradation everywhere.** Reranker rate-limited or down → fall back to RRF order. Cohere
key absent → skip reranking. This keeps the app up instead of 500-ing on a dependency hiccup.

**Security.** The `documents` table had RLS disabled (Supabase flagged it). Enabled RLS with no
policies: the backend uses the `service_role` key (which bypasses RLS), so nothing broke, while the
public `anon` key now gets no access. Also pinned `search_path` on the SQL function.

**Deploy.** Render (API) + Streamlit Community Cloud (UI) — real cloud, not a laptop. A Dockerfile +
GCP Cloud Run deploy is the planned next step to fully containerize.

---

## 4. What broke, and how I fixed it (the ugly 80%)

| # | Symptom | Root cause | Fix |
|---|---------|-----------|-----|
| 1 | Q11 (volunteer work) refused, though the answer was in the corpus | Vector search ranked the right chunk out of top-k | Added the full-text arm (hybrid + RRF) |
| 2 | Q7 (job offer) *regressed* to a refusal after hybrid | Broad lexical recall displaced the relevant chunk | Diagnosed via a corpus check ("job offer" appears 0×): it's a **corpus gap, not a retrieval bug** — stopped tuning retrieval |
| 3 | Q13 cited a source but was **wrong** ("keep working while OPT pending") | Model inferred a permission not stated in the sources | Anti-inference rule: never assert work permission unless a source explicitly grants it |
| 4 | Timeline showed **"limit 150"** for a student with a STEM degree still on **initial** OPT | Conflated *STEM-eligible* with *on the STEM extension* | Split `is_stem` from `on_stem_extension`; the 90-day limit applies on initial OPT, 150 only on the extension. Pinned with a regression test |
| 5 | Eval crashed at Q11 | Cohere trial key = 10 calls/min (429) | Reranker falls back to RRF on any error; eval paces itself under the limit |
| 6 | Migration failed: "memory required 61MB" | Stored generated column rewrote the table → rebuilt the vector index | Compute `to_tsvector` inline, no schema change |

The most instructive one is **#2**: the honest move was to *stop over-engineering retrieval* once a
coverage check showed the remaining failures were missing documents, not ranking. And **#4** is the
kind of subtle domain error (eligibility ≠ current phase) that only a real user catches and a
regression test prevents from coming back.

---

## 5. Evaluation (prove it with numbers)

Golden set of 16 real OPT questions; auto-checks for citation, disclaimer, and correct refusal,
plus eyeballed correctness. The arc:

| Stage | Score | What changed |
|-------|-------|--------------|
| Baseline (vector RAG) | 11/16 (~69%) | initial pipeline |
| + faithfulness rule | 12/16 (75%) | fixed the "cited but wrong" answer (#3) |
| + hybrid retrieval | 12/16 | fixed Q11, regressed Q7 → *diagnosed corpus gaps* |
| + reranking | 12/16 | precision infra; value hidden from a binary metric |
| **+ corpus expansion** | **15/16 (~94%)** | added travel + employment-types sources |

The one remaining "miss" (Q7, "do I need a job offer") is a **correct refusal** — no official page
states it outright, so the tool declines to assert it. In an immigration tool that restraint is the
feature. A limitation of the current metric: it's binary (answered/refused) and can't see *ranking
quality*, so reranking's gains don't show up here — RAGAS-style context-precision metrics are the
planned next measurement.

---

## 6. Limitations

- Federal sources only; no school-specific processes yet.
- Not legal advice; the tool is informational and defers to the DSO.
- Free-tier hosting: cold starts (~30-60s) and small rate limits.
- Free-tier Supabase auto-pauses the database after 7 days of no activity — a real ops reality of free infrastructure. Mitigated with a scheduled keep-alive that queries the DB every few days (and restores it if it ever paused); a production setup would use an always-on paid tier or an external uptime cron.
- The timeline parser depends on the student stating dates clearly; the "what I understood" echo is
  there so a mis-parse is visible and correctable.

---

## 7. How I'd standardize this to onboard 10 more universities

The federal core stays shared; each university becomes a thin tenant on top:

1. **Per-school source layer.** Each university's ISSS/OGA pages ingested into the same pipeline,
   tagged `metadata.tenant = "<school>"` and `metadata.tier = "school"` (federal stays `tier="federal"`).
2. **Metadata-filtered retrieval.** `hybrid_search` gets a tenant filter so a school's students see
   federal + their school's guidance, and answers prefer/label the school-specific source.
3. **Config, not code, per tenant.** A small per-school config (name, ISSS contact, source URLs,
   branding) drives ingestion and the UI — onboarding a new school is a data task, not a deploy.
4. **Eval per tenant.** Extend the golden set with a handful of school-specific questions so each
   onboarding ships with a measured accuracy number, not a hope.
5. **Ops.** Containerize (Dockerfile → Cloud Run) for predictable per-tenant deploys; keep Langfuse
   tracing so latency/cost/faithfulness are visible per school; a nightly re-crawl flags when an
   official page changed so the corpus doesn't silently go stale.

The point: the hard parts (grounding, faithfulness, deterministic date math, evals) are built once
and shared; a new "customer" is mostly their documents, a config file, and a few eval questions.
