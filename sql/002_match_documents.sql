-- OPT Navigator — Block 3 retrieval RPC (run once in the Supabase SQL editor)
-- One round-trip similarity search used by app/retrieve.py via sb.rpc(...).

create or replace function match_documents(
  query_embedding vector(1536),
  match_count int default 5
)
returns table (
  id         bigint,
  content    text,
  metadata   jsonb,
  similarity float
)
language sql stable
set search_path = public          -- pinned (not role-mutable) for security
as $$
  select
    id,
    content,
    metadata,
    1 - (embedding <=> query_embedding) as similarity
  from documents
  order by embedding <=> query_embedding
  limit match_count;
$$;
