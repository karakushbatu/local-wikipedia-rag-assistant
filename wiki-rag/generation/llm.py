import requests

OLLAMA_BASE_URL = "http://localhost:11434"
LLM_MODEL = "mistral"

SYSTEM_PROMPT = """You are a knowledgeable assistant specializing in famous people and places. \
Your answers are grounded in the provided context from Wikipedia.

Rules:
- Answer in clear, fluent prose. Be informative and specific.
- Synthesize information across multiple context sources when relevant.
- If the context contains partial information, use it and clearly indicate what is and isn't covered.
- Only say "I don't know based on the available information" if the context has NO relevant information at all.
- Do not invent facts, dates, or details not present in the context.
- Keep answers focused and well-structured. Use 2-4 paragraphs for biographical/descriptive questions."""

USER_PROMPT_TEMPLATE = """Here are relevant excerpts from Wikipedia about the topic:

{context}

Question: {question}

Write a clear, informative answer based on the excerpts above:"""


def check_ollama_available() -> bool:
    """Return True if Ollama is reachable at localhost:11434."""
    try:
        resp = requests.get(OLLAMA_BASE_URL, timeout=5)
        return resp.status_code == 200
    except Exception:
        return False


def build_context(chunks: list[dict]) -> str:
    """
    Format retrieved chunks into a readable context string.
    Each chunk is labeled with its source entity and index.
    """
    if not chunks:
        return "No relevant context found."

    parts = []
    for i, chunk in enumerate(chunks, 1):
        meta = chunk.get("metadata", {})
        entity = meta.get("entity_name", "Unknown")
        idx = meta.get("chunk_index", 0)
        parts.append(f"[Source {i}: {entity} — chunk {idx}]\n{chunk['text']}")

    return "\n\n".join(parts)


def generate_answer(query: str, chunks: list[dict]) -> str:
    """
    Build the prompt from context + query and call Ollama mistral:7b.
    Returns the generated answer string.
    """
    if not chunks:
        return "I don't know based on the available information."

    context = build_context(chunks)
    user_prompt = USER_PROMPT_TEMPLATE.format(context=context, question=query)

    full_prompt = f"{SYSTEM_PROMPT}\n\n{user_prompt}"

    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": LLM_MODEL,
        "prompt": full_prompt,
        "stream": False,
    }

    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()
    except requests.exceptions.ConnectionError:
        return (
            "Error: Cannot connect to Ollama. "
            "Please start Ollama with `ollama serve` and ensure mistral is pulled."
        )
    except requests.exceptions.Timeout:
        return "Error: The LLM request timed out. Please try again."
    except requests.exceptions.HTTPError as e:
        return f"Error: Ollama API returned an error: {e}"
    except Exception as e:
        return f"Error generating answer: {e}"
