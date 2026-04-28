"""
Standalone ingestion script.
Run with: python run_ingestion.py
Ingests all PEOPLE and PLACES into ChromaDB and tracks progress in SQLite.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.sqlite_tracker import clear_all, init_db, is_ingested, mark_failed, mark_ingested
from embeddings.embedder import embed_batch
from ingest.chunker import chunk_text
from ingest.entities import PEOPLE, PLACES
from ingest.wikipedia_fetcher import fetch_wikipedia_page
from vectorstore.chroma_store import upsert_chunks


def ingest_entity(name: str, entity_type: str) -> bool:
    """
    Ingest a single entity into ChromaDB.
    Returns True on success, False on failure.
    """
    if is_ingested(name):
        print(f"  [SKIP] Already ingested: {name}")
        return True

    print(f"  [FETCH] {name}...")
    page_data = fetch_wikipedia_page(name, entity_type)
    if page_data is None:
        mark_failed(name, entity_type, "Wikipedia page not found or disambiguation failed")
        print(f"  [FAIL] Could not fetch: {name}")
        return False

    print(f"  [CHUNK] Chunking content ({len(page_data['content'])} chars)...")
    chunks = chunk_text(
        page_data["content"],
        name,
        entity_type,
        page_data["url"],
    )
    print(f"  [CHUNK] {len(chunks)} chunks created")

    print(f"  [EMBED] Embedding {len(chunks)} chunks...")
    texts = [c["text"] for c in chunks]
    embeddings = embed_batch(texts)

    print(f"  [STORE] Upserting to ChromaDB...")
    upsert_chunks(chunks, embeddings)

    mark_ingested(name, entity_type, page_data["url"], len(chunks))
    print(f"  [OK]    Done: {name} — {len(chunks)} chunks stored")
    return True


def run_full_ingestion() -> None:
    """Ingest all PEOPLE and PLACES, print progress and summary."""
    init_db()

    total = len(PEOPLE) + len(PLACES)
    success = 0
    failed = 0
    skipped = 0

    print("=" * 60)
    print("WikiRAG — Full Ingestion Pipeline")
    print("=" * 60)

    print(f"\n📚 Ingesting {len(PEOPLE)} people...\n")
    for i, name in enumerate(PEOPLE, 1):
        print(f"[{i}/{len(PEOPLE)}] {name}")
        if is_ingested(name):
            print(f"  [SKIP] Already ingested")
            skipped += 1
            continue
        ok = ingest_entity(name, "person")
        if ok:
            success += 1
        else:
            failed += 1

    print(f"\n🏛️ Ingesting {len(PLACES)} places...\n")
    for i, name in enumerate(PLACES, 1):
        print(f"[{i}/{len(PLACES)}] {name}")
        if is_ingested(name):
            print(f"  [SKIP] Already ingested")
            skipped += 1
            continue
        ok = ingest_entity(name, "place")
        if ok:
            success += 1
        else:
            failed += 1

    print("\n" + "=" * 60)
    print("Ingestion complete!")
    print(f"  ✅ Success: {success}")
    print(f"  ❌ Failed:  {failed}")
    print(f"  ⏭️ Skipped: {skipped}")
    print(f"  📦 Total:   {total}")
    print("=" * 60)
    print("\nRun the app with: streamlit run app/streamlit_app.py")


if __name__ == "__main__":
    run_full_ingestion()
