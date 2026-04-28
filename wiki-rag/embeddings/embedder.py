import asyncio
import requests

OLLAMA_BASE_URL = "http://localhost:11434"
EMBED_MODEL = "nomic-embed-text"
CONCURRENT_REQUESTS = 8  # parallel embedding requests to Ollama


def embed_text(text: str) -> list[float]:
    """
    Embed a single text string using Ollama nomic-embed-text.
    Calls the Ollama REST API directly via raw HTTP — no SDK.
    """
    url = f"{OLLAMA_BASE_URL}/api/embeddings"
    payload = {"model": EMBED_MODEL, "prompt": text}

    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()["embedding"]
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Cannot connect to Ollama. Make sure Ollama is running: `ollama serve`"
        )
    except requests.exceptions.Timeout:
        raise RuntimeError("Ollama embedding request timed out.")
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"Ollama API error: {e}")
    except KeyError:
        raise RuntimeError("Unexpected response format from Ollama embeddings API.")


async def _embed_one_async(session, semaphore, text: str) -> list[float]:
    """Async single embedding call with concurrency limit."""
    import httpx
    async with semaphore:
        response = await session.post(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": text},
            timeout=60,
        )
        response.raise_for_status()
        return response.json()["embedding"]


async def _embed_batch_async(texts: list[str]) -> list[list[float]]:
    """Embed all texts concurrently, up to CONCURRENT_REQUESTS at a time."""
    import httpx
    semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)
    async with httpx.AsyncClient() as session:
        tasks = [_embed_one_async(session, semaphore, t) for t in texts]
        return await asyncio.gather(*tasks)


def embed_batch(texts: list[str]) -> list[list[float]]:
    """
    Embed a list of texts in parallel using async HTTP requests.
    Falls back to sequential if httpx is not installed.
    """
    if not texts:
        return []

    try:
        import httpx  # noqa: F401
        return asyncio.run(_embed_batch_async(texts))
    except ImportError:
        # Fallback: sequential with requests
        print("[WARNING] httpx not installed, falling back to sequential embedding.")
        print("[WARNING] Run: pip install httpx   for much faster ingestion.")
        return [embed_text(t) for t in texts]
