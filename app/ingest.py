"""Block 2-3 — ingest the OPT corpus into Supabase (pgvector).

Pipeline:  load (.md / .txt / .html / .pdf)  ->  chunk  ->  embed  ->  upsert.

Every chunk keeps `metadata.source` = the canonical URL of the document (read
from data/raw/sources.json) so the RAG layer can cite the real page. PDFs also
keep their page number.

Run (after filling .env and creating the table from sql/001_schema.sql):
    python -m app.ingest            # ingest everything in data/raw
    python -m app.ingest --reset    # delete existing rows first, then ingest
    python -m app.ingest --dry-run  # load + chunk only; print stats, no embeds
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from langchain_community.document_loaders import BSHTMLLoader, PyPDFLoader, TextLoader
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from supabase import create_client

from app.config import settings

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
SOURCES = RAW_DIR / "sources.json"

CHUNK_SIZE = 800
CHUNK_OVERLAP = 120
EMBED_BATCH = 100   # texts per embedding request
UPSERT_BATCH = 200  # rows per insert


def _manifest() -> dict:
    """filename -> {url, title, ...} (provenance for citations)."""
    return json.loads(SOURCES.read_text()) if SOURCES.exists() else {}


def load_documents() -> list[Document]:
    """Load every supported file in data/raw, tagging metadata.source = URL."""
    manifest = _manifest()
    docs: list[Document] = []

    for path in sorted(RAW_DIR.iterdir()):
        if path.name in {"sources.json", ".gitkeep"} or path.is_dir():
            continue

        suffix = path.suffix.lower()
        if suffix == ".pdf":
            loaded = PyPDFLoader(str(path)).load()           # one Document per page
        elif suffix in {".html", ".htm"}:
            loaded = BSHTMLLoader(str(path)).load()
        elif suffix in {".md", ".txt"}:
            loaded = TextLoader(str(path), encoding="utf-8").load()
        else:
            print(f"  skip (unsupported): {path.name}")
            continue

        meta = manifest.get(path.name, {})
        url = meta.get("url", path.name)
        for d in loaded:
            d.metadata["source"] = url            # cite the real page, not the filename
            d.metadata["file"] = path.name
            if meta.get("title"):
                d.metadata["title"] = meta["title"]
            # PyPDFLoader sets metadata["page"]; keep it for "p.N" citations.
        docs.extend(loaded)
        print(f"  loaded {len(loaded):>3} doc(s) from {path.name}  -> {url}")

    return docs


def chunk(docs: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    chunks = splitter.split_documents(docs)
    print(f"{len(docs)} docs -> {len(chunks)} chunks")
    return chunks


def embed_and_upsert(chunks: list[Document], reset: bool = False) -> int:
    emb = OpenAIEmbeddings(model=settings.EMBEDDING_MODEL, api_key=settings.OPENAI_API_KEY)
    sb = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

    if reset:
        sb.table("documents").delete().neq("id", 0).execute()
        print("reset: cleared existing rows in 'documents'")

    texts = [c.page_content for c in chunks]

    vectors: list[list[float]] = []
    for i in range(0, len(texts), EMBED_BATCH):
        batch = texts[i : i + EMBED_BATCH]
        vectors.extend(emb.embed_documents(batch))
        print(f"  embedded {min(i + EMBED_BATCH, len(texts))}/{len(texts)}")

    rows = [
        {"content": c.page_content, "metadata": c.metadata, "embedding": v}
        for c, v in zip(chunks, vectors)
    ]

    inserted = 0
    for i in range(0, len(rows), UPSERT_BATCH):
        batch = rows[i : i + UPSERT_BATCH]
        sb.table("documents").insert(batch).execute()
        inserted += len(batch)
        print(f"  inserted {inserted}/{len(rows)}")

    return inserted


def main() -> None:
    ap = argparse.ArgumentParser(description="Ingest the OPT corpus into Supabase.")
    ap.add_argument("--reset", action="store_true", help="delete existing rows first")
    ap.add_argument("--dry-run", action="store_true", help="load + chunk only, no embeds")
    args = ap.parse_args()

    print(f"Loading from {RAW_DIR} ...")
    docs = load_documents()
    if not docs:
        raise SystemExit("No documents found in data/raw — nothing to ingest.")
    chunks = chunk(docs)

    if args.dry_run:
        print("\n--- sample chunk ---")
        print(chunks[0].metadata)
        print(chunks[0].page_content[:400])
        print("\ndry-run: skipping embed + upsert.")
        return

    settings.validate()  # ensure OpenAI + Supabase creds are present
    n = embed_and_upsert(chunks, reset=args.reset)
    print(f"\nDone. Inserted {n} chunks into Supabase 'documents'.")


if __name__ == "__main__":
    main()
