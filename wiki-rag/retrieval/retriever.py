from embeddings.embedder import embed_text
from ingest.entities import PEOPLE, PLACES
from ingest.chunker import _is_low_quality
from retrieval.classifier import classify_query, _PERSON_TOKENS, _PLACE_TOKENS
from vectorstore.chroma_store import query as chroma_query


def _filter_quality(chunks: list[dict]) -> list[dict]:
    """Remove bibliography/reference chunks from results."""
    return [c for c in chunks if not _is_low_quality(c["text"])]


def _find_mentioned_entities(query: str) -> tuple[list[str], list[str]]:
    """
    Return lists of person names and place names explicitly mentioned in the query.
    Checks full names first, then individual tokens (last names etc.).
    """
    q_lower = query.lower()
    mentioned_people = []
    mentioned_places = []

    for name in PEOPLE:
        if name.lower() in q_lower and name not in mentioned_people:
            mentioned_people.append(name)

    for name in PLACES:
        if name.lower() in q_lower and name not in mentioned_places:
            mentioned_places.append(name)

    # Token-level fallback — collect unique full names matched by token
    if not mentioned_people:
        seen = set()
        for token, full_name in _PERSON_TOKENS:
            if token in q_lower and full_name not in seen:
                seen.add(full_name)
                mentioned_people.append(full_name)

    if not mentioned_places:
        seen = set()
        for token, full_name in _PLACE_TOKENS:
            if token in q_lower and full_name not in seen:
                seen.add(full_name)
                mentioned_places.append(full_name)

    return mentioned_people, mentioned_places


def retrieve(query: str, n_results: int = 8) -> list[dict]:
    """
    Retrieve the most relevant chunks for a user query.

    - If specific entity names are mentioned, fetch chunks filtered to those
      entities first, then pad with general similarity search.
    - For generic queries, fall back to type-filtered similarity search.
    """
    if not query.strip():
        return []

    query_embedding = embed_text(query)
    entity_type = classify_query(query)

    mentioned_people, mentioned_places = _find_mentioned_entities(query)
    mentioned_all = mentioned_people + mentioned_places

    # If specific entities are mentioned, retrieve targeted chunks
    if mentioned_all:
        from vectorstore.chroma_store import get_collection

        collection = get_collection()
        chunks_per_entity = max(2, n_results // len(mentioned_all))
        targeted = []
        seen_texts = set()

        for entity_name in mentioned_all:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=min(chunks_per_entity, collection.count()),
                where={"entity_name": entity_name},
                include=["documents", "metadatas", "distances"],
            )
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ):
                if doc not in seen_texts:
                    seen_texts.add(doc)
                    targeted.append({"text": doc, "metadata": meta, "distance": dist})

        targeted = _filter_quality(targeted)
        targeted.sort(key=lambda c: c["distance"])

        if len(targeted) >= n_results:
            return targeted[:n_results]

        # Pad with general search if not enough targeted results
        general = _filter_quality(chroma_query(
            query_embedding,
            entity_type=entity_type if entity_type != "both" else None,
            n_results=n_results * 2,
        ))
        for chunk in general:
            if chunk["text"] not in seen_texts:
                seen_texts.add(chunk["text"])
                targeted.append(chunk)

        targeted.sort(key=lambda c: c["distance"])
        return targeted[:n_results]

    # No specific entity mentioned — general similarity search
    if entity_type == "both":
        person_chunks = _filter_quality(chroma_query(query_embedding, entity_type="person", n_results=6))
        place_chunks = _filter_quality(chroma_query(query_embedding, entity_type="place", n_results=6))

        seen_texts = set()
        merged = []
        for chunk in person_chunks + place_chunks:
            if chunk["text"] not in seen_texts:
                seen_texts.add(chunk["text"])
                merged.append(chunk)

        merged.sort(key=lambda c: c["distance"])
        return merged[:n_results]

    results = _filter_quality(chroma_query(query_embedding, entity_type=entity_type, n_results=n_results * 2))
    return results[:n_results]
