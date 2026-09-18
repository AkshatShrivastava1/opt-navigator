-- OPT Navigator — Week 14: user feedback capture (run once in the Supabase SQL editor)
-- Stores a thumbs up/down + optional comment for an answer, so real usage can drive
-- future eval/corpus improvements. Additive only — no change to existing tables.

create table if not exists feedback (
  id          bigserial primary key,
  created_at  timestamptz not null default now(),
  question    text,
  answer      text,
  rating      text,            -- 'up' | 'down'
  comment     text,
  sources     jsonb            -- the source URLs shown with the answer (for context)
);

-- Newest-first reads for a future review dashboard.
create index if not exists feedback_created_at_idx on feedback (created_at desc);

-- Same posture as the documents table: RLS on, and only the service key (used by the
-- backend) can write/read. No anon policy is defined, so the anon key sees nothing.
alter table feedback enable row level security;
