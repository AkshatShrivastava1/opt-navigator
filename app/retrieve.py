"""Block 4 — vector retrieval over Supabase (pgvector).

Implemented later this week. Calls the `match_documents` RPC created in
sql/002_match_documents.sql. Week 2 adds BM25 + reranking on top of this.
"""
from __future__ import annotations

from langchain_openai import OpenAIEmbeddings
from supabase import create_client

from app.config import settings

_emb = OpenAIEmbeddings(model=settings.EMBEDDING_MODEL)
_sb = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)


def retrieve(query: str, k: int = 5) -> list[dict]:
    """Return the k most similar chunks: list of {content, metadata, similarity}."""
    qvec = _emb.embed_query(query)
    res = _sb.rpc(
        "match_documents",
        {"query_embedding": qvec, "match_count": k},
    ).execute()
    return res.data


if __name__ == "__main__":
    for hit in retrieve("How many days of unemployment am I allowed on post-completion OPT?"):
        print(round(hit["similarity"], 3), hit["metadata"].get("source"))
