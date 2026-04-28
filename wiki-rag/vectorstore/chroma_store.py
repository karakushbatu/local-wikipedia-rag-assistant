"""
ChromaDB vector store using Option B: ONE collection with metadata filtering.

Design rationale: A single "wiki_rag" collection with entity_type metadata
simplifies the architecture, supports cross-type queries (mixed questions
about both people and places), and leverages ChromaDB's built-in metadata
filtering (where={"entity_type": "person"}) instead of maintaining two
separate collections. This is more scalable and flexible.
"""

import os
from typing import Optional
import chromadb
from chromadb.config import Settings

COLLECTION_NAME = "wiki_rag"
CHROMA_PERSIST_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "chroma_db",
)

_client: Optional[chromadb.PersistentClient] = None
_collection: Optional[chromadb.Collection] = None


def _get_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        os.makedirs(CHROMA_PERSIST_PATH, exist_ok=True)
        _client = chromadb.PersistentClient(path=CHROMA_PERSIST_PATH)
    return _client


def get_collection() -> chromadb.Collection:
    """Get or create the single wiki_rag collection."""
    global _collection
    if _collection is None:
        client = _get_client()
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def _make_id(entity_name: str, chunk_index: int) -> str:
    """Normalize entity name to a stable document ID."""
    normalized = entity_name.lower().replace(" ", "_").replace("'", "").replace(",", "")
    return f"{normalized}_{chunk_index}"


def upsert_chunks(chunks: list[dict], embeddings: list[list[float]]) -> None:
    """
    Upsert chunk documents and their embeddings into ChromaDB.
    chunks: list of { "text": str, "metadata": dict }
    embeddings: parallel list of embedding vectors
    """
    collection = get_collection()

    ids = []
    documents = []
    metadatas = []
    embedding_list = []

    for chunk, embedding in zip(chunks, embeddings):
        doc_id = _make_id(
            chunk["metadata"]["entity_name"],
            chunk["metadata"]["chunk_index"],
        )
        ids.append(doc_id)
        documents.append(chunk["text"])
        metadatas.append(chunk["metadata"])
        embedding_list.append(embedding)

    if ids:
        collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embedding_list,
        )


def query(
    embedding: list[float],
    entity_type: Optional[str] = None,
    n_results: int = 5,
) -> list[dict]:
    """
    Query the vector store for similar chunks.

    entity_type: "person", "place", or None (search both)
    Returns list of { text, metadata, distance }
    """
    collection = get_collection()

    total_docs = collection.count()
    if total_docs == 0:
        return []

    safe_n = min(n_results, total_docs)

    where_filter = None
    if entity_type in ("person", "place"):
        where_filter = {"entity_type": entity_type}

    kwargs = {
        "query_embeddings": [embedding],
        "n_results": safe_n,
        "include": ["documents", "metadatas", "distances"],
    }
    if where_filter:
        kwargs["where"] = where_filter

    results = collection.query(**kwargs)

    output = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        output.append({"text": doc, "metadata": meta, "distance": dist})

    return output


def count_documents(entity_type: Optional[str] = None) -> int:
    """Count documents in the collection, optionally filtered by entity_type."""
    collection = get_collection()

    if entity_type is None:
        return collection.count()

    results = collection.get(
        where={"entity_type": entity_type},
        include=["metadatas"],
    )
    return len(results["ids"])


def reset_collection() -> None:
    """Delete and recreate the collection, wiping all data."""
    global _collection
    client = _get_client()
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    _collection = None
    get_collection()
