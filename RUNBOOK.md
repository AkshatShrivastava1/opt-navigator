# RUNBOOK — finishing Week 1 (Block 2–3 ingest)

Status of the pipeline:

- Repo scaffolded (`app/` package), deps in `requirements.txt`, corpus in `data/raw/` (7 official docs → ~93 chunks).
- Supabase `opt-navigator`: `documents` table + `match_documents` function + pgvector are **already created**.
- Remaining: run the ingest (embed + upsert) **on your Mac** — the embed step calls the OpenAI API, which must run from an unrestricted network.

## One-time local setup

```bash
cd ~/Documents/CICStep\ Project
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Fill in `.env`

`SUPABASE_URL` and `SUPABASE_SERVICE_KEY` are already set. Add your OpenAI key:

```
OPENAI_API_KEY=sk-...
```

> The OpenAI account needs a small credit balance (~$5). With $0 credit the ingest fails with `insufficient_quota`. The ingest itself costs ~$0.0005.

## Run

```bash
# sanity check — should print: env OK
python -c "from app.config import settings; settings.validate(); print('env OK')"

# load -> chunk -> embed -> upsert  (use --reset to clear before re-ingesting)
python -m app.ingest --reset
```

Expected:

```
7 docs -> 93 chunks
  embedded 93/93
  inserted 93/93
Done. Inserted 93 chunks into Supabase 'documents'.
```

## Verify the rows landed

In the Supabase SQL Editor (or ask me — I can check via the connection):

```sql
select count(*) as chunks, count(distinct metadata->>'source') as sources
from documents;
-- expect ~93 chunks across 7 sources
```

Quick retrieval smoke test (after `pip install`):

```bash
python -c "from app.retrieve import retrieve; \
[print(round(h['similarity'],3), h['metadata']['source']) \
 for h in retrieve('how many unemployment days on post-completion OPT?')]"
```

## Troubleshooting

- `insufficient_quota` → add OpenAI credit.
- `Missing required env vars` → a value in `.env` is blank.
- `relation \"documents\" does not exist` → re-run `sql/001_schema.sql` and `sql/002_match_documents.sql`.
- Re-ingesting duplicates rows → use `python -m app.ingest --reset`.

## Optional cleanup

The Linux sandbox that scaffolded this repo can't delete files on the macOS mount, so `.git/` may contain a few harmless `*.lock.stale` / `tmp_obj_*` files. Safe to remove on your Mac:

```bash
find .git -name '*.lock.stale' -delete
git gc --prune=now   # cleans leftover loose objects
```
