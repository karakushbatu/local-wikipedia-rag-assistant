import time
from typing import Optional
import requests

DELAY_SECONDS = 1
MAX_RETRIES = 3

# Wikipedia REST API — more reliable than the wikipedia Python library
WIKI_API_URL = "https://en.wikipedia.org/w/api.php"
WIKI_REST_URL = "https://en.wikipedia.org/api/rest_v1/page/summary"

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "WikiRAG/1.0 (educational project; local use only)",
    "Accept": "application/json",
})
SESSION.verify = False  # disable SSL verification for proxy/corporate environments
requests.packages.urllib3.disable_warnings()


def _get_page_content(title: str) -> Optional[dict]:
    """
    Fetch full page content via MediaWiki Action API.
    Returns dict with title, content, url or None.
    """
    params = {
        "action": "query",
        "prop": "extracts|info",
        "titles": title,
        "explaintext": True,
        "inprop": "url",
        "format": "json",
        "redirects": 1,
    }
    resp = SESSION.get(WIKI_API_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    pages = data.get("query", {}).get("pages", {})
    page = next(iter(pages.values()))

    if "missing" in page:
        return None

    content = page.get("extract", "")
    if not content:
        return None

    canonical_title = page.get("title", title)
    url = f"https://en.wikipedia.org/wiki/{canonical_title.replace(' ', '_')}"

    return {"title": canonical_title, "content": content, "url": url}


def _search_title(name: str) -> Optional[str]:
    """Search Wikipedia for the best matching title."""
    params = {
        "action": "query",
        "list": "search",
        "srsearch": name,
        "srlimit": 1,
        "format": "json",
    }
    resp = SESSION.get(WIKI_API_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    results = data.get("query", {}).get("search", [])
    if results:
        return results[0]["title"]
    return None


def fetch_wikipedia_page(name: str, entity_type: str) -> Optional[dict]:
    """
    Fetch a Wikipedia page for a given entity name using the MediaWiki API.
    Retries up to MAX_RETRIES times on transient errors.
    Returns dict with title, content, url, type — or None on failure.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            time.sleep(DELAY_SECONDS)

            # First try exact title
            data = _get_page_content(name)

            # If not found, search for the best match
            if data is None:
                found_title = _search_title(name)
                if found_title:
                    print(f"[WARNING] '{name}' not found directly, trying '{found_title}'")
                    data = _get_page_content(found_title)

            if data is None:
                print(f"[ERROR] Wikipedia page not found for '{name}'")
                return None

            data["type"] = entity_type
            return data

        except Exception as e:
            print(f"[WARNING] Attempt {attempt}/{MAX_RETRIES} failed for '{name}': {e}")
            if attempt < MAX_RETRIES:
                time.sleep(DELAY_SECONDS * attempt)
            else:
                print(f"[ERROR] All retries exhausted for '{name}'")
                return None

    return None
