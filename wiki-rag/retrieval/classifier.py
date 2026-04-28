from ingest.entities import PEOPLE, PLACES

PERSON_KEYWORDS = [
    "who", "born", "died", "career", "life", "person",
    "scientist", "artist", "athlete", "musician", "actor",
    "inventor", "philosopher", "discover", "wrote", "painted",
    "played", "famous person", "biography", "he", "she",
    "his", "her", "politician", "leader", "president", "compare",
]

PLACE_KEYWORDS = [
    "where", "located", "place", "city", "country", "tower",
    "mountain", "river", "building", "monument", "temple",
    "wall", "canyon", "pyramid", "statue", "island", "ocean",
    "site", "landmark", "attraction", "visit", "travel", "located in",
]

# Last name / short alias lookup built from entity lists at import time
_PERSON_TOKENS: list[tuple[str, str]] = []
_PLACE_TOKENS: list[tuple[str, str]] = []

for _name in PEOPLE:
    for _token in _name.lower().split():
        if len(_token) > 3:          # skip short words like "da", "van"
            _PERSON_TOKENS.append((_token, _name))

for _name in PLACES:
    for _token in _name.lower().split():
        if len(_token) > 3:
            _PLACE_TOKENS.append((_token, _name))


def classify_query(query: str) -> str:
    """
    Classify a user query as 'person', 'place', or 'both'.

    Strategy:
    1. Check full entity names first.
    2. Check individual name tokens (catches "Messi", "Einstein", "Colosseum").
    3. Fall back to keyword scoring.
    4. Default → 'both'.
    """
    q_lower = query.lower()

    # Step 1 — full name match
    found_person = any(name.lower() in q_lower for name in PEOPLE)
    found_place = any(name.lower() in q_lower for name in PLACES)

    # Step 2 — partial token match (last names, single-word place names)
    if not found_person:
        found_person = any(token in q_lower for token, _ in _PERSON_TOKENS)
    if not found_place:
        found_place = any(token in q_lower for token, _ in _PLACE_TOKENS)

    if found_person and found_place:
        return "both"
    if found_person:
        return "person"
    if found_place:
        return "place"

    # Step 3 — keyword scoring
    person_score = sum(1 for kw in PERSON_KEYWORDS if kw in q_lower)
    place_score = sum(1 for kw in PLACE_KEYWORDS if kw in q_lower)

    if person_score > place_score:
        return "person"
    if place_score > person_score:
        return "place"

    return "both"
