-- OPT Navigator — Block 3 schema (run once in the Supabase SQL editor)
-- Enables pgvector and creates the documents table + similarity index.

create extension if not exists vector;

create table if not exists documents (
  id        bigserial primary key,
  content   text,
  metadata  jsonb,
  embedding vector(1536)          -- 1536 = OpenAI text-embedding-3-small
);

-- Approximate nearest-neighbour index for cosine distance.
-- ivfflat (per the build plan). For a small corpus you may instead use hnsw:
--   create index on documents using hnsw (embedding vector_cosine_ops);
create index if not exists documents_embedding_ivfflat
  on documents using ivfflat (embedding vector_cosine_ops) with (lists = 100);

-- Optional: speed up metadata lookups (e.g. filter by source url).
create index if not exists documents_metadata_gin
  on documents using gin (metadata);
