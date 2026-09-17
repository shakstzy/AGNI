"""DuckDuckGo search — the universal third party that maps free-text
addresses and region names to canonical Redfin URLs.

Why we need this at all: Redfin's own /stingray/do/location-autocomplete
endpoint is Akamai-walled to unauthenticated callers (confirmed 403
across header variants), and Zillow's only public address resolver is
the slug-redirect chain (which works for it). For Redfin we need an
external search engine to do address -> candidate-URL resolution.

We use the `ddgs` library (formerly duckduckgo-search) rather than
parsing DDG's HTML ourselves. The HTML endpoint returns a 202
interstitial after the first call until a vqd token round-trips, and
the library handles that token negotiation, backoff, and User-Agent
rotation. Lightweight (no native deps beyond requests) and MIT-licensed.

Public API:
    find_first(query, site, *, url_pattern) -> str | None
        Run `site:<site> <query>` and return the first hit whose URL
        matches `url_pattern` (compiled regex). None if nothing matches.

    find_all(query, site, *, url_pattern, limit=10) -> list[str]
        Same as above, returns up to `limit` matches in DDG result order.
"""
from __future__ import annotations

import re

try:
    from ddgs import DDGS  # ddgs >= 6.0 (renamed from duckduckgo-search)
except ImportError:  # pragma: no cover
    from duckduckgo_search import DDGS  # older name


import json
import os

_CACHE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", ".cache", "search_cache.json"
)


def _load_cache() -> dict[str, list[str]]:
    if not os.path.exists(_CACHE_FILE):
        return {}
    try:
        with open(_CACHE_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def _save_cache(cache: dict[str, list[str]]) -> None:
    try:
        os.makedirs(os.path.dirname(_CACHE_FILE), exist_ok=True)
        with open(_CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
    except Exception:
        pass


def find_all(query: str, site: str, *, url_pattern: re.Pattern[str],
             limit: int = 10) -> list[str]:
    """site:<site> <query> -> list of result URLs matching `url_pattern`."""
    cache_key = f"{site}:{query}"
    cache = _load_cache()
    if cache_key in cache:
        matches = [u for u in cache[cache_key] if url_pattern.search(u)]
        if matches:
            return matches[:limit]

    clean_q = re.sub(r"[,#?]", " ", query).strip()
    candidate_queries = [
        f"site:{site} {clean_q}",
        f"{site} {clean_q}",
        f"site:{site} {query}",
    ]

    all_found: list[str] = []
    seen: set[str] = set()

    for q in candidate_queries:
        try:
            results = DDGS().text(q, max_results=max(limit * 3, 10))
        except Exception:
            results = []
        if not results:
            continue
        for r in results:
            url = r.get("href") or r.get("link") or ""
            if not url or url in seen:
                continue
            seen.add(url)
            all_found.append(url)
        if any(url_pattern.search(u) for u in all_found):
            break

    if all_found:
        cache[cache_key] = all_found
        _save_cache(cache)

    matches = [u for u in all_found if url_pattern.search(u)]
    return matches[:limit]


def find_first(query: str, site: str, *, url_pattern: re.Pattern[str]) -> str | None:
    matches = find_all(query, site, url_pattern=url_pattern, limit=1)
    return matches[0] if matches else None
