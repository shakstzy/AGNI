"""Cross-source dedupe for Redfin + Zillow homes.

Match precedence:
  1. Same-source primary key (zpid for Zillow, property_id for Redfin).
  2. Lat/lng proximity <=25m AND beds match AND sqft within 5%.
  3. Normalized address+zip AND beds match AND sqft within 5%
     (the missing-coords fallback - Zillow sometimes drops coords on
     unmapped/off-market listings).
"""
from __future__ import annotations

import math
import re
from collections.abc import Iterable


_EARTH_R_M = 6371000.0


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
    return 2 * _EARTH_R_M * math.asin(math.sqrt(a))


def _primary_key(home: dict) -> tuple | None:
    if home.get("zpid"):
        return ("zpid", str(home["zpid"]))
    if home.get("property_id"):
        return ("rid", str(home["property_id"]))
    return None


_STREET_TYPE_NORMS = {
    "saint": "st", "street": "st", "avenue": "ave", "boulevard": "blvd",
    "road": "rd", "drive": "dr", "lane": "ln", "court": "ct",
    "place": "pl", "circle": "cir", "trail": "trl", "highway": "hwy",
    "parkway": "pkwy", "terrace": "ter", "way": "way", "cove": "cv",
    "loop": "loop", "square": "sq",
}
_DIRECTION_NORMS = {
    "north": "n", "south": "s", "east": "e", "west": "w",
    "northeast": "ne", "northwest": "nw", "southeast": "se", "southwest": "sw",
}
_UNIT_RE = re.compile(
    r"(?:\b(?:unit|apt|apartment|ste|suite)\.?\b|#)\s*(\S+)",
    re.IGNORECASE,
)


def extract_unit(addr: str | None) -> str | None:
    if not addr:
        return None
    s = re.sub(r"[.,]", " ", addr.lower())
    m = _UNIT_RE.search(s)
    return m.group(1).strip().lower() if m else None


def normalize_address(addr: str | None) -> str:
    if not addr:
        return ""
    s = addr.lower()
    s = re.sub(r"[.,]", " ", s)
    s = _UNIT_RE.sub("", s)
    tokens = []
    for t in s.split():
        t = t.strip()
        if not t:
            continue
        if t in _STREET_TYPE_NORMS:
            t = _STREET_TYPE_NORMS[t]
        if t in _DIRECTION_NORMS:
            t = _DIRECTION_NORMS[t]
        tokens.append(t)
    return " ".join(tokens)


def _units_compatible(a: dict, b: dict) -> bool:
    ua = extract_unit(a.get("address"))
    ub = extract_unit(b.get("address"))
    if ua and ub and ua != ub:
        return False
    return True


def _beds_compatible(a: dict, b: dict) -> bool:
    if a.get("beds") is not None and b.get("beds") is not None:
        return a["beds"] == b["beds"]
    return True


def _sqft_compatible(a: dict, b: dict, *, tolerance: float = 0.05) -> bool:
    sa, sb = a.get("sqft"), b.get("sqft")
    if sa and sb:
        return abs(sa - sb) / max(sa, sb) <= tolerance
    return True


def _approx_match(a: dict, b: dict, *, max_meters: float = 25.0) -> bool:
    if not (_beds_compatible(a, b) and _sqft_compatible(a, b)
            and _units_compatible(a, b)):
        return False
    la, lna = a.get("lat"), a.get("lng")
    lb, lnb = b.get("lat"), b.get("lng")
    if la is not None and lna is not None and lb is not None and lnb is not None:
        if haversine_m(la, lna, lb, lnb) <= max_meters:
            return True
        return False
    addr_a = normalize_address(a.get("address"))
    addr_b = normalize_address(b.get("address"))
    if not addr_a or not addr_b or addr_a != addr_b:
        return False
    za = str(a.get("zip") or "").strip()
    zb = str(b.get("zip") or "").strip()
    if not za or not zb or za != zb:
        return False
    return True


def merge(*lists: Iterable[dict], max_meters: float = 25.0) -> list[dict]:
    merged: list[dict] = []
    keys_seen: dict[tuple, int] = {}
    for batch in lists:
        for home in batch:
            pk = _primary_key(home)
            if pk and pk in keys_seen:
                merged[keys_seen[pk]].setdefault("_other_sources", []).append(home)
                continue
            matched_idx = None
            for i, existing in enumerate(merged):
                if _approx_match(home, existing, max_meters=max_meters):
                    matched_idx = i
                    break
            if matched_idx is not None:
                merged[matched_idx].setdefault("_other_sources", []).append(home)
                continue
            home = dict(home)
            home.setdefault("_source", home.get("source"))
            merged.append(home)
            if pk:
                keys_seen[pk] = len(merged) - 1
    return merged
