-- OPT Navigator — Week 2 Block 1: hybrid retrieval (full-text + vector, RRF)
-- Run once in the Supabase SQL editor. No schema change: to_tsvector is computed inline,
-- which avoids a table rewrite (that would rebuild the ivfflat index and exceed the free
-- tier's maintenance_work_mem). When the corpus grows, switch to a stored `fts` column +
-- GIN index on a tier with more memory.
--
-- The full-text arm converts the query to OR semantics ('volunteer' | 'unpaid' | ...) so a
-- chunk matching ANY salient term is a candidate; RRF + the vector arm handle precision.

create or replace function public.hybrid_search(
  query_text text,
  query_embedding vector(1536),
  match_count int default 5,
  rrf_k int default 50
)
returns table (id bigint, content text, metadata jsonb, similarity float)
language sql stable
set search_path = public
as $$
  with q as (
    select to_tsquery('english',
             nullif(regexp_replace(
               coalesce(websearch_to_tsquery('english', query_text)::text, ''),
               '&', '|', 'g'), '')) as tsq
  ),
  vector_arm as (
    select id, row_number() over (order by embedding <=> query_embedding) as rnk
    from documents
    order by embedding <=> query_embedding
    limit 30
  ),
  fts_arm as (
    select id, rnk from (
      select d.id,
             row_number() over (
               order by ts_rank(to_tsvector('english', d.content), q.tsq) desc
             ) as rnk
      from documents d, q
      where q.tsq is not null
        and to_tsvector('english', d.content) @@ q.tsq
    ) ranked
    where rnk <= 30
  ),
  fused as (
    select coalesce(v.id, f.id) as id,
           coalesce(1.0 / (rrf_k + v.rnk), 0.0)
         + coalesce(1.0 / (rrf_k + f.rnk), 0.0) as similarity
    from vector_arm v
    full outer join fts_arm f on v.id = f.id
  )
  select d.id, d.content, d.metadata, fused.similarity
  from fused
  join documents d on d.id = fused.id
  order by fused.similarity desc
  limit match_count;
$$;
