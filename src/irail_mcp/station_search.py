"""Offline station search using bundled station data.

Loads stations.json once at import time, then searches with accent-folded,
case-insensitive substring matching across all name variants.
"""

import json
import unicodedata
from functools import lru_cache
from importlib import resources


def _strip_accents(text: str) -> str:
    """Remove accents/diacritics from text via NFKD decomposition."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _normalize(text: str) -> str:
    """Normalize text for search: strip accents and casefold."""
    return _strip_accents(text).casefold()


@lru_cache(maxsize=1)
def _load_stations() -> list[dict]:
    """Load and pre-process station data from bundled JSON.

    Each station gets a '_search_text' field: all name variants joined and
    normalized for fast substring matching.
    """
    data_files = resources.files("irail_mcp.data")
    stations_file = data_files.joinpath("stations.json")
    raw = json.loads(stations_file.read_text(encoding="utf-8"))

    for station in raw:
        names = [
            station.get("name", ""),
            station.get("alternative_fr", ""),
            station.get("alternative_nl", ""),
            station.get("alternative_de", ""),
            station.get("alternative_en", ""),
        ]
        station["_search_text"] = _normalize(" ".join(n for n in names if n))

    return raw


def search_stations(query: str) -> list[dict]:
    """Search stations by name with accent-insensitive substring matching.

    Args:
        query: Search string (e.g., "Liege", "bruxelles", "Gent")

    Returns:
        List of matching station dicts with keys: uri, name,
        alternative_fr/nl/de/en, longitude, latitude, country_code.
    """
    if not query or not query.strip():
        return []

    normalized_query = _normalize(query.strip())
    stations = _load_stations()

    results = []
    for station in stations:
        if normalized_query in station["_search_text"]:
            # Return a copy without the internal _search_text field
            result = {k: v for k, v in station.items() if k != "_search_text"}
            results.append(result)

    return results
