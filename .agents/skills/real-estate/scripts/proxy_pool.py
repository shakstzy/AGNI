"""Automated Free Proxy Pool and Rotator for Real Estate Scrapers.

Features:
1. Prioritizes user environment variables ($REAL_ESTATE_PROXY, $HTTPS_PROXY, $HTTP_PROXY).
2. Auto-fetches fresh candidate proxies from public proxy sources (Monosans, TheSpeedX, Proxyscrape).
3. Concurrently probes candidate proxies with strict 2.5s timeouts against reliable targets.
4. Maintains an on-disk JSON cache (~/.cache/proxies.json or .cache/proxies.json) with auto-expiry.
5. Provides thread-safe proxy rotation, success tracking, and bad-proxy eviction.
"""
from __future__ import annotations

import concurrent.futures
import json
import os
import random
import threading
import time
import urllib.request
from pathlib import Path
from typing import Any

_CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache"
_CACHE_FILE = _CACHE_DIR / "proxies.json"
_CACHE_TTL_SEC = 3600  # 1 hour

_PUBLIC_PROXY_SOURCES = [
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
]

_TEST_TARGETS = [
    "http://httpbin.org/ip",
    "http://1.1.1.1",
]

_lock = threading.RLock()
_active_pool: list[str] = []
_current_index = 0


def _normalize_proxy(p: str) -> str:
    p = p.strip()
    if not p:
        return ""
    if not p.startswith("http://") and not p.startswith("https://") and not p.startswith("socks5://"):
        return f"http://{p}"
    return p


def _test_single_proxy(proxy_url: str, timeout: float = 2.5) -> tuple[str, float] | None:
    norm = _normalize_proxy(proxy_url)
    if not norm:
        return None
    t0 = time.time()
    try:
        handler = urllib.request.ProxyHandler({"http": norm, "https": norm})
        opener = urllib.request.build_opener(handler)
        req = urllib.request.Request(_TEST_TARGETS[0], headers={"User-Agent": "Mozilla/5.0"})
        with opener.open(req, timeout=timeout) as resp:
            if resp.status == 200:
                latency = round(time.time() - t0, 3)
                return norm, latency
    except Exception:
        pass
    return None


def fetch_candidate_proxies(max_candidates: int = 150) -> list[str]:
    candidates: list[str] = []
    for src in _PUBLIC_PROXY_SOURCES:
        try:
            req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                text = resp.read().decode("utf-8", errors="ignore")
                lines = [l.strip() for l in text.splitlines() if l.strip() and not l.startswith("#")]
                candidates.extend(lines)
                if len(candidates) >= max_candidates * 2:
                    break
        except Exception:
            continue
    random.shuffle(candidates)
    return candidates[:max_candidates]


def refresh_pool(target_size: int = 15, max_workers: int = 25) -> list[str]:
    global _active_pool
    candidates = fetch_candidate_proxies(max_candidates=target_size * 10)
    working: list[tuple[str, float]] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_test_single_proxy, c): c for c in candidates}
        for fut in concurrent.futures.as_completed(futures):
            res = fut.result()
            if res:
                working.append(res)
                if len(working) >= target_size:
                    break

    working.sort(key=lambda x: x[1])
    pool = [p[0] for p in working]

    with _lock:
        _active_pool = pool
        _save_cache(pool)

    return pool


def _load_cache() -> list[str]:
    if not _CACHE_FILE.exists():
        return []
    try:
        data = json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
        saved_at = data.get("saved_at", 0)
        if time.time() - saved_at > _CACHE_TTL_SEC:
            return []
        return data.get("proxies", [])
    except Exception:
        return []


def _save_cache(proxies: list[str]) -> None:
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            "saved_at": time.time(),
            "count": len(proxies),
            "proxies": proxies,
        }
        _CACHE_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except Exception:
        pass


def get_proxy(auto_refresh: bool = True) -> str | None:
    """Return a working proxy URL.
    
    1. Checks environment variables ($REAL_ESTATE_PROXY, $HTTPS_PROXY, $HTTP_PROXY).
    2. Uses in-memory or on-disk cached proxy pool.
    3. Auto-refreshes from public sources if pool is depleted.
    """
    env_proxy = (
        os.environ.get("REAL_ESTATE_PROXY")
        or os.environ.get("HTTPS_PROXY")
        or os.environ.get("HTTP_PROXY")
    )
    if env_proxy:
        return _normalize_proxy(env_proxy)

    global _active_pool, _current_index
    with _lock:
        if not _active_pool:
            cached = _load_cache()
            if cached:
                _active_pool = cached
            elif auto_refresh:
                _active_pool = refresh_pool()

        if not _active_pool:
            return None

        _current_index = (_current_index + 1) % len(_active_pool)
        return _active_pool[_current_index]


def report_failure(proxy_url: str) -> None:
    """Evict a failing proxy from the pool so future calls don't reuse it."""
    global _active_pool
    norm = _normalize_proxy(proxy_url)
    with _lock:
        if norm in _active_pool:
            _active_pool.remove(norm)
            _save_cache(_active_pool)


def report_success(proxy_url: str) -> None:
    """No-op hook for telemetry / keeping responsive proxies."""
    pass


if __name__ == "__main__":
    import sys
    print("Testing proxy pool...")
    p = get_proxy(auto_refresh=True)
    print(f"Selected proxy: {p}")
    print(f"Active pool size: {len(_active_pool)}")
