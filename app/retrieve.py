"""Retrieval over Supabase: hybrid search + optional cross-encoder reranking.

- Hybrid (Week 2): fuses full-text (lexical) and vector (semantic) search with
  Reciprocal Rank Fusion via the `hybrid_search` RPC (sql/003_hybrid_search.sql).
- Reranking (Week 3): retrieve a wide net (fetch_k), then re-score (query, chunk)
  pairs with Cohere Rerank and keep the top k. This restores precision that the
  broad lexical arm can cost (e.g., the Q7 "do I need a job offer" regression).

Graceful fallback: with no COHERE_API_KEY set, retrieval returns the top-k RRF
results unchanged, so nothing breaks.
"""
from __future__ import annotations

from langchain_openai import OpenAIEmbeddings
from supabase import create_client

from app.config import settings

_emb = OpenAIEmbeddings(model=settings.EMBEDDING_MODEL, api_key=settings.OPENAI_API_KEY)
_sb = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

# Optional Cohere reranker — only built if a key is present.
_co = None
if settings.COHERE_API_KEY:
    try:
        import cohere

        _co = cohere.Client(settings.COHERE_API_KEY)
    except Exception:
        _co = None


def _rerank(query: str, hits: list[dict], k: int) -> list[dict]:
    """Re-score candidates with Cohere Rerank; fall back to RRF order if unavailable."""
    if not _co or not hits:
        return hits[:k]
    try:
        res = _co.rerank(
            model=settings.RERANK_MODEL,
            query=query,
            documents=[h["content"] for h in hits],
            top_n=k,
        )
    except Exception:
        # Reranker unavailable or rate-limited -> degrade gracefully to RRF order.
        return hits[:k]
    out = []
    for r in res.results:
        hit = dict(hits[r.index])
        hit["rerank_score"] = r.relevance_score
        out.append(hit)
    return out


def retrieve(query: str, k: int = 5, fetch_k: int = 20) -> list[dict]:
    """Hybrid-retrieve a wide net (fetch_k), then rerank to the top k.

    Returns a list of {id, content, metadata, similarity[, rerank_score]}.
    """
    qvec = _emb.embed_query(query)
    res = _sb.rpc(
        "hybrid_search",
        {"query_text": query, "query_embedding": qvec, "match_count": fetch_k},
    ).execute()
    return _rerank(query, res.data, k)


if __name__ == "__main__":
    for h in retrieve("Do I need a job offer to apply for OPT?"):
        score = h.get("rerank_score", h.get("similarity"))
        print(round(score, 4), h["metadata"].get("source"))
