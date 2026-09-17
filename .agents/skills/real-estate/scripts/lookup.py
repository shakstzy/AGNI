"""Address-to-house lookup. Free-text address in, Redfin + Zillow data out,
side-by-side plus a merged top-level view.

Resolution path:
  1. Redfin: free-text -> autocomplete (canonical /<ST>/<City>/.../home/<id>)
  2. Zillow: free-text -> slugify and follow /homes/<slug>/ -> 301
             /homedetails/<zpid>_zpid/
  3. Hit each property page (1 live hit per site, max 2 hits total).
  4. Merge: prefer values from the source that has them; flag conflicts.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys
from typing import Any

import redfin
import search_engine
import zillow
import zillow_parse

RF_PROPERTY_RE = re.compile(r"redfin\.com/[A-Z]{2}/[^/]+/[^/]+/home/\d+")
ZW_PROPERTY_RE = re.compile(r"zillow\.com/homedetails/[^/]+/\d+_zpid")


def _zillow_slug(address: str) -> str | None:
    s = (address or "").strip()
    if not s:
        return None
    s = re.sub(r"[,]+", " ", s)
    s = re.sub(r"\s+", "-", s)
    return s


_STREET_NUM_RE = re.compile(r"^\s*(\d+)\b")


def _street_number(address: str) -> str | None:
    m = _STREET_NUM_RE.match(address)
    return m.group(1) if m else None


def _street_descriptor(address: str) -> tuple[str | None, str | None]:
    if not address:
        return None, None
    s = re.sub(r"[,]+", " ", address).lower()
    tokens = s.split()
    if not tokens:
        return None, None
    start = 0
    while start < len(tokens) and re.fullmatch(r"\d+", tokens[start]):
        start += 1
    directions = {"n", "s", "e", "w", "ne", "nw", "se", "sw",
                  "north", "south", "east", "west",
                  "northeast", "northwest", "southeast", "southwest"}
    while start < len(tokens) and tokens[start] in directions:
        start += 1
    if start >= len(tokens):
        return None, None
    name = re.sub(r"[^a-z0-9]+", "", tokens[start])
    second = re.sub(r"[^a-z0-9]+", "", tokens[start + 1]) if start + 1 < len(tokens) else None
    return (name or None), (second or None)


def _is_redfin_property_url(s: str) -> bool:
    return bool(RF_PROPERTY_RE.search(s or ""))


def _is_zillow_property_url(s: str) -> bool:
    return bool(ZW_PROPERTY_RE.search(s or ""))


_RF_PROPERTY_URL_PATTERN = re.compile(r"redfin\.com/[A-Z]{2}/[^/]+/[^/]+/home/\d+")


def _url_has_street_num(url: str, num: str) -> bool:
    return bool(re.search(rf"/{re.escape(num)}-", url))


def _url_has_token(url: str, token: str) -> bool:
    return bool(re.search(rf"(?:^|[/-]){re.escape(token)}(?:[/-]|$)", url, re.IGNORECASE))


def find_redfin_url(address_or_url: str) -> str | None:
    """Resolve to a canonical Redfin property URL via DuckDuckGo
    `site:redfin.com <address>`, with a street-number AND street-name
    filter so a search for '5509 Casco Walk' can't return '5501 Casco
    Walk' (indexed neighbor) or '5509 Hibiscus Dr' (different street).

    Returns None when no result satisfies both filters — new-build /
    off-market listings often aren't indexed, and the caller should
    accept --redfin-url for those.
    """
    if _is_redfin_property_url(address_or_url):
        return address_or_url
    street_num = _street_number(address_or_url)
    street_name, street_type = _street_descriptor(address_or_url)

    _SUFFIX_MAP = {
        "lane": "ln", "ln": "lane",
        "street": "st", "st": "street",
        "road": "rd", "rd": "road",
        "drive": "dr", "dr": "drive",
        "court": "ct", "ct": "court",
        "avenue": "ave", "ave": "avenue",
        "boulevard": "blvd", "blvd": "boulevard",
        "circle": "cir", "cir": "circle",
        "place": "pl", "pl": "place",
        "terrace": "ter", "ter": "terrace",
        "parkway": "pkwy", "pkwy": "parkway",
        "trail": "trl", "trl": "trail",
        "highway": "hwy", "hwy": "highway",
        "way": "wy", "wy": "way",
    }

    candidates = search_engine.find_all(
        address_or_url, "redfin.com",
        url_pattern=_RF_PROPERTY_URL_PATTERN, limit=10,
    )
    for url in candidates:
        if street_num and not _url_has_street_num(url, street_num):
            continue
        if street_name and not _url_has_token(url, street_name):
            continue
        if street_type:
            alias = _SUFFIX_MAP.get(street_type.lower())
            if not (_url_has_token(url, street_type) or (alias and _url_has_token(url, alias))):
                continue
        return url
    return None


def find_zillow_url(address_or_url: str) -> str | None:
    """Resolve to a canonical Zillow homedetails URL via slug-redirect.

    Zillow 301-redirects /homes/<num>-<street>-<city>-<ST>-<zip>/ to
    /homedetails/<zpid>_zpid/. No third-party search needed.
    """
    if _is_zillow_property_url(address_or_url):
        return address_or_url
    slug = _zillow_slug(address_or_url)
    if not slug:
        return None
    try:
        s = zillow._get_session()
        chain_url = f"https://www.zillow.com/homes/{slug}/"
        for _ in range(3):
            r = s.get(chain_url, timeout=20, allow_redirects=False)
            loc = r.headers.get("Location") or r.headers.get("location")
            if not loc:
                break
            if loc.startswith("/"):
                loc = "https://www.zillow.com" + loc
            if _is_zillow_property_url(loc):
                return loc
            chain_url = loc
    except Exception:
        return None
    return None


# Per-field aggregation rules: numerics get averaged (and side-by-side reported
# with a spread%); categoricals pass through whichever source has them with a
# match/mismatch flag; collections take the source with more data.
_NUMERIC_FIELDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    # (field, aliases on either source)
    ("price", ()),
    ("redfin_estimate", ()),
    ("zestimate", ()),
    ("rent_estimate", ()),
    ("rent_zestimate", ()),
    ("tax_assessed_value", ()),
    ("price_per_sqft", ()),
    ("monthly_hoa_fee", ("hoa_per_month",)),
    ("annual_homeowners_insurance", ()),
    ("property_tax_rate", ()),
    ("beds", ("bedrooms",)),
    ("baths", ("bathrooms",)),
    ("full_baths", ("bathroomsFull",)),
    ("half_baths", ("bathroomsHalf",)),
    ("sqft", ("livingArea",)),
    ("year_built", ()),
    ("lot_size", ()),
    ("days_on_market", ("time_on_zillow",)),
    ("lat", ("latitude",)),
    ("lng", ("longitude",)),
    ("walk_score", ()),
    ("transit_score", ()),
    ("bike_score", ()),
)

_CATEGORICAL_FIELDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("address", ()),
    ("city", ()),
    ("state", ()),
    ("zip", ()),
    ("home_type", ("property_type",)),
    ("home_status", ("status",)),
    ("mls_id", ()),
    ("mls_name", ()),
)

# Fields where a literal 0 means "no data" (a house can't have 0 beds / 0
# sqft / cost $0). Zillow sometimes returns 0 for these on sold/off-market
# listings; treat that 0 as missing so it doesn't drag the aggregate mean
# down (e.g. 2.5 baths averaged with a bogus 0 -> 1.25). HOA is NOT here:
# $0 HOA is legitimate.
_ZERO_IS_MISSING = frozenset({
    "price", "redfin_estimate", "zestimate", "rent_estimate", "rent_zestimate",
    "tax_assessed_value", "price_per_sqft", "property_tax_rate",
    "beds", "baths", "full_baths", "half_baths", "sqft", "year_built", "lot_size",
})


def _aggregate_views(rf: dict, zw: dict) -> tuple[dict, list[dict]]:
    """Build (aggregate, comparison) for a Redfin + Zillow pair.

    aggregate: flat dict of canonical values per field. Numeric fields get
    the mean of the two sources when both populate; otherwise the sole value.
    Categorical fields pass through whichever source has a value (Redfin
    wins ties since its property pages parse more reliably). Collections
    (photos, history, schools, listing_agent, ...) take the source with
    more entries.

    comparison: per-field side-by-side list. Each row carries both source
    values plus either a numeric `aggregate` + `spread_pct` or a string
    `match` flag. Rows are sorted by spread_pct desc so disagreements
    jump out. Single-source rows surface as `redfin_only` / `zillow_only`.
    """
    rf = rf if isinstance(rf, dict) and not rf.get("error") else {}
    zw = zw if isinstance(zw, dict) and not zw.get("error") else {}

    aggregate: dict[str, Any] = {}
    comparison: list[dict] = []

    def _first_val(src: dict, key: str, aliases: tuple[str, ...]) -> Any:
        for k in (key, *aliases):
            v = src.get(k)
            if v is not None:
                return v
        return None

    # Numeric fields: both reported, mean aggregated, spread% surfaced
    for field, aliases in _NUMERIC_FIELDS:
        rfv = _first_val(rf, field, aliases)
        zwv = _first_val(zw, field, aliases)
        # Coerce bogus 0 -> missing for fields that can't legitimately be 0.
        if field in _ZERO_IS_MISSING:
            if rfv == 0:
                rfv = None
            if zwv == 0:
                zwv = None
        if rfv is None and zwv is None:
            continue
        try:
            rfn = float(rfv) if rfv is not None else None
            zwn = float(zwv) if zwv is not None else None
        except (TypeError, ValueError):
            rfn = zwn = None
        if rfn is not None and zwn is not None:
            agg: Any = (rfn + zwn) / 2.0
            # round to int when both sources are integral-like
            if isinstance(rfv, int) and isinstance(zwv, int):
                agg = round(agg)
            elif field in ("beds", "year_built", "sqft", "lot_size",
                           "days_on_market", "full_baths", "half_baths",
                           "walk_score", "transit_score", "bike_score"):
                agg = round(agg)
            else:
                agg = round(agg, 4)
            mean_abs = abs((rfn + zwn) / 2.0) or 1.0
            spread = round(abs(rfn - zwn) / mean_abs * 100, 2)
            aggregate[field] = agg
            comparison.append({
                "field": field, "redfin": rfv, "zillow": zwv,
                "aggregate": agg, "spread_pct": spread,
            })
        elif rfn is not None:
            aggregate[field] = rfv
            comparison.append({"field": field, "redfin": rfv, "zillow": None,
                                "aggregate": rfv, "source": "redfin_only"})
        elif zwn is not None:
            aggregate[field] = zwv
            comparison.append({"field": field, "redfin": None, "zillow": zwv,
                                "aggregate": zwv, "source": "zillow_only"})
        else:
            # both non-null but non-numeric (unlikely for these fields)
            aggregate[field] = rfv if rfv is not None else zwv

    # Categorical fields: passthrough + match flag
    for field, aliases in _CATEGORICAL_FIELDS:
        rfv = _first_val(rf, field, aliases)
        zwv = _first_val(zw, field, aliases)
        if rfv is None and zwv is None:
            continue
        if rfv is not None and zwv is not None:
            match = "ok" if str(rfv).strip().lower() == str(zwv).strip().lower() else "mismatch"
            aggregate[field] = rfv  # passthrough; both visible in comparison
            comparison.append({"field": field, "redfin": rfv, "zillow": zwv, "match": match})
        elif rfv is not None:
            aggregate[field] = rfv
            comparison.append({"field": field, "redfin": rfv, "zillow": None, "source": "redfin_only"})
        else:
            aggregate[field] = zwv
            comparison.append({"field": field, "redfin": None, "zillow": zwv, "source": "zillow_only"})

    # Collections: take whichever source has more data; both are still
    # readable under result['redfin']/result['zillow'].
    aggregate["price_history"] = (rf.get("price_history") or zw.get("price_history")
                                    or rf.get("history") or [])
    aggregate["tax_history"] = rf.get("tax_history") or zw.get("tax_history") or []
    aggregate["schools"] = rf.get("schools") or zw.get("schools") or []
    aggregate["nearby_homes"] = rf.get("nearby_homes") or zw.get("nearby_homes") or []
    aggregate["open_houses"] = (rf.get("open_houses") or []) + (zw.get("open_houses") or [])

    rf_agent = rf.get("listing_agent") or {}
    zw_agent = zw.get("listing_agent") or {}
    rf_score = sum(1 for v in rf_agent.values() if v) if isinstance(rf_agent, dict) else 0
    zw_score = sum(1 for v in zw_agent.values() if v) if isinstance(zw_agent, dict) else 0
    aggregate["listing_agent"] = rf_agent if rf_score >= zw_score else zw_agent

    rf_photos = rf.get("photos") or []
    zw_photos = zw.get("photos") or []
    aggregate["photos"] = rf_photos if len(rf_photos) >= len(zw_photos) else zw_photos
    aggregate["photo_count"] = max(len(rf_photos), len(zw_photos)) or None

    # Zillow-leaning enrichments (descriptions, climate, room features, MLS)
    for k in ("description", "virtual_tour_url", "climate_risk", "nearby_cities",
             "nearby_neighborhoods", "interior_features", "exterior_features",
             "parking_features", "garage_spaces", "heating", "cooling",
             "appliances", "fireplace", "flooring", "stories", "view_description",
             "pool_features", "is_new_construction"):
        if zw.get(k) is not None:
            aggregate.setdefault(k, zw[k])
        elif rf.get(k) is not None:
            aggregate.setdefault(k, rf[k])

    # Redfin-leaning enrichments (AI summary, parcel info, history, etc.)
    for k in ("ai_summary", "commute", "weather", "sun_exposure", "parcel_info",
             "parcel_boundaries", "zoning", "permits", "popularity",
             "price_drop", "neighborhood_stats", "newest_listings_nearby",
             "tour_insights", "buying_power", "home_highlight_tags",
             "avm_historical", "risk_factors", "amenities", "comps", "apn",
             "list_date", "sold_date"):
        if rf.get(k) is not None:
            aggregate.setdefault(k, rf[k])
        elif zw.get(k) is not None:
            aggregate.setdefault(k, zw[k])

    # Sort comparison: numerics with biggest spread first, then mismatches,
    # then matches, then single-source rows.
    def _sort_key(row: dict) -> tuple:
        if "spread_pct" in row:
            return (0, -row["spread_pct"])
        if row.get("match") == "mismatch":
            return (1, 0)
        if row.get("match") == "ok":
            return (2, 0)
        return (3, 0)
    comparison.sort(key=_sort_key)
    return aggregate, comparison


CACHE_DIR = Path.home() / ".cache" / "hades" / "real-estate"


def _lookup_cache_slug(address: str) -> str:
    s = address.strip().lower()
    s = re.sub(r"\b(lane)\b", "ln", s)
    s = re.sub(r"\b(street)\b", "st", s)
    s = re.sub(r"\b(court)\b", "ct", s)
    s = re.sub(r"\b(drive)\b", "dr", s)
    s = re.sub(r"\b(avenue)\b", "ave", s)
    s = re.sub(r"\b(boulevard)\b", "blvd", s)
    s = re.sub(r"\b(road)\b", "rd", s)
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def _get_lookup_cache(address: str, include_raw: bool) -> dict | None:
    try:
        slug = _lookup_cache_slug(address)
        tag = "_raw" if include_raw else ""
        cache_file = CACHE_DIR / f"{slug}{tag}.json"
        if not cache_file.exists():
            # Try raw cache if non-raw was requested
            if not include_raw:
                cache_file = CACHE_DIR / f"{slug}_raw.json"
        if cache_file.exists():
            data = json.loads(cache_file.read_text("utf-8"))
            if data and not data.get("diagnostics", {}).get("redfin_error") and not (data.get("redfin") or {}).get("error"):
                return data
    except Exception:
        pass
    return None


def _save_lookup_cache(address: str, include_raw: bool, data: dict):
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        slug = _lookup_cache_slug(address)
        tag = "_raw" if include_raw else ""
        cache_file = CACHE_DIR / f"{slug}{tag}.json"
        cache_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), "utf-8")
    except Exception:
        pass


def lookup(address: str, *, include_raw: bool = False,
           redfin_url: str | None = None, zillow_url: str | None = None) -> dict:
    if not redfin_url and not zillow_url:
        cached = _get_lookup_cache(address, include_raw)
        if cached:
            return cached

    rf_url = redfin_url or find_redfin_url(address)
    zw_url = zillow_url or find_zillow_url(address)

    rf: dict
    if not rf_url:
        rf = {"error": (
            "no exact Redfin URL found via DuckDuckGo (site:redfin.com). "
            "Pass --redfin-url <url> if you have it."
        )}
    else:
        try:
            rf = redfin.property_details(rf_url, include_raw=include_raw)
        except Exception as e:
            rf = {"error": str(e), "url": rf_url}

    zw: dict
    if not zw_url:
        zw = {"error": (
            "no Zillow URL found via slug redirect. Pass --zillow-url <url> if you have it."
        )}
    else:
        try:
            zw = zillow.property_details(zw_url, include_raw=include_raw)
        except Exception as e:
            zw = {"error": str(e), "url": zw_url}

    aggregate, comparison = _aggregate_views(rf, zw)
    diagnostics: dict[str, Any] = {}
    if rf.get("error"):
        diagnostics["redfin_error"] = rf["error"]
    if zw.get("error"):
        diagnostics["zillow_error"] = zw["error"]
    rf_status = (rf or {}).get("status")
    rf_off_market = isinstance(rf_status, str) and "off market" in rf_status.lower()
    if rf_off_market:
        diagnostics["redfin_off_market"] = (
            "Redfin gates schools / tax_history / price_history / listing_agent / "
            "nearby_homes for off-market listings. Field emptiness here is real, "
            "not a parser bug."
        )
    if (rf.get("error") or rf_off_market) and not zw.get("error"):
        diagnostics["zillow_lazy_load_gap"] = (
            "Zillow loads schools / tax_history / price_history via separate "
            "GraphQL queries that fire AFTER initial page render. Our scraper "
            "only sees initial HTML, so those fields are unavailable from "
            "Zillow. Workaround: pass --redfin-url for an active listing."
        )

    # Degraded Zillow record detector. When a listing goes off-market / sold,
    # Zillow sometimes drops the rich structure data and mis-tags the record
    # as homeType=LOT / homeStatus=OTHER, which zeroes out baths, photos, etc.
    # even though the home clearly has bedrooms. Flag it so a 0/missing bath
    # count reads as "bad Zillow record" not "parser bug".
    if not zw.get("error"):
        zw_home_type = (zw.get("home_type") or "")
        zw_beds = zw.get("beds")
        zw_baths = zw.get("baths")
        looks_like_lot = str(zw_home_type).upper() in ("LOT", "LAND", "")
        has_structure = isinstance(zw_beds, (int, float)) and zw_beds and zw_beds > 0
        zeroed_baths = (zw_baths in (0, None)) and has_structure
        if (looks_like_lot and has_structure) or zeroed_baths:
            diagnostics["zillow_degraded_record"] = (
                f"Zillow has this tagged home_type={zw_home_type or 'null'} / "
                f"home_status={zw.get('home_status')!r} but it has {zw_beds} bedrooms — "
                "a degraded off-market/sold record. Zillow zeroes baths / photos / "
                "specs under that tag. Trust Redfin for specs here; the aggregate "
                "already drops Zillow's bogus zeros."
            )

    rf_addr = (rf.get("address") or "") if isinstance(rf, dict) else ""
    zw_addr = (zw.get("address") or "") if isinstance(zw, dict) else ""
    addr_match = "ok"
    if rf_addr and zw_addr and rf_addr.split(",")[0].strip().lower() != zw_addr.split(",")[0].strip().lower():
        addr_match = "mismatch"
    if rf.get("error") and zw.get("error"):
        addr_match = "neither_resolved"
    elif rf.get("error") or zw.get("error"):
        addr_match = "single_source"
    result = {
        "input_address": address,
        "redfin_url": rf_url,
        "zillow_url": zw_url,
        "address_match": addr_match,
        "redfin": rf,
        "zillow": zw,
        "aggregate": aggregate,
        "comparison": comparison,
        "diagnostics": diagnostics,
    }
    if not rf.get("error") and not zw.get("error"):
        _save_lookup_cache(address, include_raw, result)
    return result


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(prog="lookup")
    ap.add_argument("address", help='free-text address, OR a Redfin/Zillow URL')
    ap.add_argument("--include-raw", action="store_true",
                    help="include the full nested API payloads from each source")
    ap.add_argument("--aggregate-only", action="store_true",
                    help="print only the aggregate + comparison, not the per-source payloads")
    ap.add_argument("--comparison-only", action="store_true",
                    help="print only the comparison list (per-field side-by-side)")
    ap.add_argument("--redfin-url", help="skip resolution; use this Redfin URL directly")
    ap.add_argument("--zillow-url", help="skip resolution; use this Zillow URL directly")
    args = ap.parse_args(argv)

    result = lookup(
        args.address, include_raw=args.include_raw,
        redfin_url=args.redfin_url, zillow_url=args.zillow_url,
    )
    if args.comparison_only:
        out = result["comparison"]
    elif args.aggregate_only:
        out = {"aggregate": result["aggregate"], "comparison": result["comparison"]}
    else:
        out = result
    json.dump(out, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
