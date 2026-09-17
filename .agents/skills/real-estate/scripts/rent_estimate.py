"""Rent estimate from Zillow rental comps, triangulated against Redfin's
own RentalEstimate when available.

Algorithm:
  1. Resolve target home -> lat/lng/sqft/beds (uses lookup.py). Side
     benefit: lookup also surfaces Redfin's predicted rent if the listing
     is active, which we report alongside our comp-based number.
  2. Build a small bbox around target (default 1.0 mile).
  3. zillow.search() with status=for-rent in that bbox.
  4. Filter comps: distance, EXACT bed match.
  5. If fewer than `target_comp_count` (default 40) pass, expand the
     radius and try again. Max expansion: `max_radius_miles` (default 3.0).
  6. Compute median + trimmed-mean $/sqft from the final comp set.
  7. Multiply target sqft -> low / mid / high estimate.

Filter rules:
  - **beds: EXACT match** by default. A 4-bed rental is not a comp for
    a 2-bed estimate. `--beds-tolerance N` available for power users.
  - **distance: within current radius** at each expansion step (haversine).
  - **sqft: no filter.** Exact-beds matching naturally bounds the sqft
    range (4-bed homes don't come in 600 sqft), and rental sqft on Zillow
    is the noisiest field, so adding a band cost more comps than it saved.

`redfin_rent_estimate` is the second, independent number — when both
agree we have a strong rent signal, when they diverge we flag it.
"""
from __future__ import annotations

import math
import statistics

import zillow
import lookup
from dedupe import haversine_m


_METERS_PER_MILE = 1609.344


def _bbox_around(lat: float, lng: float, miles: float) -> tuple[float, float, float, float]:
    miles = max(0.0, miles)
    dlat = miles / 69.0
    dlng = miles / (69.0 * max(math.cos(math.radians(lat)), 0.05))
    return (lat + dlat, lng + dlng, lat - dlat, lng - dlng)


def _filter_comps(comps: list[dict], *, target_lat: float, target_lng: float,
                  target_beds: int | None, max_miles: float,
                  beds_tolerance: int = 0) -> list[dict]:
    """Keep only comps that pass distance + beds filters.

    - beds: |comp.beds - target.beds| <= beds_tolerance (default 0 = exact)
    - distance: haversine <= max_miles
    - both price AND sqft must be present (we compute $/sqft from them)
    """
    out = []
    for c in comps:
        clat, clng = c.get("lat"), c.get("lng")
        if clat is None or clng is None:
            continue
        dist_m = haversine_m(target_lat, target_lng, float(clat), float(clng))
        dist_mi = dist_m / _METERS_PER_MILE
        if dist_mi > max_miles:
            continue
        if target_beds is not None and c.get("beds") is not None:
            if abs(int(c["beds"]) - int(target_beds)) > beds_tolerance:
                continue
        if not c.get("price") or not c.get("sqft"):
            continue
        c_sqft = float(c["sqft"])
        c = dict(c)
        c["distance_miles"] = round(dist_mi, 3)
        c["price_per_sqft"] = round(float(c["price"]) / c_sqft, 4)
        out.append(c)
    out.sort(key=lambda x: x["distance_miles"])
    return out


def _trim_mean(values: list[float], pct: float = 0.1) -> float | None:
    if not values:
        return None
    n = len(values)
    drop = max(1, int(n * pct)) if n >= 5 else 0
    sorted_vals = sorted(values)
    trimmed = sorted_vals[drop: n - drop] if drop else sorted_vals
    if not trimmed:
        trimmed = sorted_vals
    return sum(trimmed) / len(trimmed)


def _triangulate(zillow_mid: float | None, redfin_rent: float | None) -> dict:
    if zillow_mid is None and redfin_rent is None:
        return {"verdict": None, "consensus_rent": None, "spread_pct": None}
    if zillow_mid is None:
        return {"verdict": "single_redfin", "consensus_rent": redfin_rent, "spread_pct": None}
    if redfin_rent is None:
        return {"verdict": "single_zillow", "consensus_rent": zillow_mid, "spread_pct": None}
    avg = (zillow_mid + redfin_rent) / 2.0
    spread = abs(zillow_mid - redfin_rent) / avg if avg else 0
    if spread <= 0.10:
        verdict = "strong"
        consensus = round(avg)
    elif spread <= 0.25:
        verdict = "soft"
        consensus = round(min(zillow_mid, redfin_rent))
    else:
        verdict = "diverged"
        consensus = round(avg)
    return {"verdict": verdict, "consensus_rent": consensus, "spread_pct": round(spread * 100, 1)}


def _radius_steps(start: float, cap: float) -> list[float]:
    """Generate the radius-expansion ladder. Start at `start` and grow by
    50% each step, capped at `cap`. The cap is always included as the
    final step.
    """
    out: list[float] = []
    r = max(0.1, start)
    while r < cap:
        out.append(round(r, 3))
        r *= 1.5
    out.append(round(cap, 3))
    # Dedupe in case start >= cap.
    seen: list[float] = []
    for v in out:
        if v not in seen:
            seen.append(v)
    return seen


def estimate_rent(
    address: str,
    *,
    radius_miles: float = 1.0,
    max_radius_miles: float = 3.0,
    target_comp_count: int = 40,
    beds_tolerance: int = 0,
    redfin_url: str | None = None,
    zillow_url: str | None = None,
    target_override: dict | None = None,
) -> dict:
    redfin_rent = None
    if target_override:
        target = target_override
    else:
        looked = lookup.lookup(address, redfin_url=redfin_url, zillow_url=zillow_url)
        agg = looked.get("aggregate") or {}
        target = {
            "address": agg.get("address") or address,
            "lat": agg.get("lat"),
            "lng": agg.get("lng"),
            "sqft": agg.get("sqft"),
            "beds": agg.get("beds"),
            "zip": agg.get("zip"),
            "_lookup": looked,
        }
        redfin_rent = agg.get("rent_estimate")

    if target.get("lat") is None or target.get("lng") is None:
        return {
            "address": target.get("address") or address,
            "error": ("could not resolve target lat/lng. Pass --redfin-url or "
                      "--zillow-url so the lookup can resolve, or check the address."),
        }

    target_beds = int(target["beds"]) if target.get("beds") else None
    target_sqft = target.get("sqft")

    # Auto-expand radius until we have target_comp_count valid comps, or
    # we hit max_radius_miles. Each step is a fresh Zillow search at the
    # larger bbox; we keep the last (largest) result set.
    radius_attempts: list[dict] = []
    comps: list[dict] = []
    used_radius = radius_miles
    for radius in _radius_steps(radius_miles, max_radius_miles):
        bbox = _bbox_around(float(target["lat"]), float(target["lng"]), radius)
        try:
            rentals = zillow.search(
                query=None, bbox=bbox, status="for-rent",
                min_beds=(target_beds - beds_tolerance) if target_beds else None,
                max_price=None,
            )
            raw_comps = rentals.get("homes") or []
        except Exception as e:
            raw_comps = []
            radius_attempts.append({
                "radius_miles": radius,
                "error": str(e),
                "raw_zillow_results": 0,
                "comps_after_filter": 0,
            })
            break

        comps = _filter_comps(
            raw_comps,
            target_lat=float(target["lat"]), target_lng=float(target["lng"]),
            target_beds=target_beds, max_miles=radius,
            beds_tolerance=beds_tolerance,
        )
        used_radius = radius
        radius_attempts.append({
            "radius_miles": radius,
            "raw_zillow_results": len(raw_comps),
            "comps_after_filter": len(comps),
        })
        if len(comps) >= target_comp_count:
            break

    if len(comps) < 3:
        out = {
            "address": target.get("address"),
            "comp_count": len(comps),
            "comps": comps,
            "radius_attempts": radius_attempts,
            "error": (
                f"only {len(comps)} comps after expanding to {used_radius} mi "
                f"with exact beds match. Try --beds-tolerance 1, "
                f"--max-radius-miles 5.0, or pass --rent-total directly."
            ),
            "target": {"lat": target["lat"], "lng": target["lng"],
                       "sqft": target.get("sqft"), "beds": target.get("beds")},
            "redfin_rent_estimate": redfin_rent,
        }
        if redfin_rent is not None:
            out.update(_triangulate(None, redfin_rent))
            out["estimated_rent_mid"] = float(redfin_rent)
            out["estimated_rent_low"] = round(float(redfin_rent) * 0.90, 2)
            out["estimated_rent_high"] = round(float(redfin_rent) * 1.10, 2)
        return out

    pps_values = [c["price_per_sqft"] for c in comps]
    median_pps = statistics.median(pps_values)
    trim_pps = _trim_mean(pps_values)
    comp_prices = [c["price"] for c in comps if c.get("price")]
    if target_sqft and target_sqft > 0:
        target_sqft = float(target_sqft)
        low = round(min(pps_values) * target_sqft)
        mid = round(median_pps * target_sqft)
        high = round(max(pps_values) * target_sqft)
        trim_estimate = round(trim_pps * target_sqft) if trim_pps else None
    elif comp_prices:
        low = round(min(comp_prices))
        mid = round(statistics.median(comp_prices))
        high = round(max(comp_prices))
        trim_estimate = round(_trim_mean(comp_prices)) if _trim_mean(comp_prices) else mid
    else:
        low = mid = high = trim_estimate = None

    triangulation = _triangulate(mid, redfin_rent)

    return {
        "source": "zillow",
        "address": target.get("address"),
        "target": {
            "lat": target["lat"], "lng": target["lng"],
            "sqft": target.get("sqft"), "beds": target.get("beds"),
            "zip": target.get("zip"),
        },
        "radius_miles_used": used_radius,
        "radius_attempts": radius_attempts,
        "target_comp_count": target_comp_count,
        "comp_count": len(comps),
        "comp_count_met_target": len(comps) >= target_comp_count,
        "beds_tolerance": beds_tolerance,
        "median_price_per_sqft": round(median_pps, 4),
        "trimmed_mean_price_per_sqft": round(trim_pps, 4) if trim_pps else None,
        "estimated_rent_low": low,
        "estimated_rent_mid": mid,
        "estimated_rent_high": high,
        "estimated_rent_trimmed": trim_estimate,
        "redfin_rent_estimate": redfin_rent,
        "triangulation_verdict": triangulation["verdict"],
        "consensus_rent": triangulation["consensus_rent"],
        "spread_pct": triangulation["spread_pct"],
        "comps": [
            {
                "address": c.get("address"),
                "city": c.get("city"),
                "zip": c.get("zip"),
                "price": c.get("price"),
                "sqft": c.get("sqft"),
                "beds": c.get("beds"),
                "baths": c.get("baths"),
                "url": c.get("url"),
                "distance_miles": c.get("distance_miles"),
                "price_per_sqft": c.get("price_per_sqft"),
            }
            for c in comps
        ],
    }


def main(argv=None):
    import argparse
    import json
    import sys
    ap = argparse.ArgumentParser(prog="rent-estimate")
    ap.add_argument("address")
    ap.add_argument("--radius-miles", type=float, default=1.0,
                    help="starting radius (default 1.0); expands automatically until --target-comps reached")
    ap.add_argument("--max-radius-miles", type=float, default=3.0,
                    help="cap on auto-expand (default 3.0)")
    ap.add_argument("--target-comps", dest="target_comp_count", type=int, default=40,
                    help="stop expanding once this many valid comps are in (default 40)")
    ap.add_argument("--beds-tolerance", type=int, default=0,
                    help="beds difference allowed (default 0 = exact match)")
    ap.add_argument("--redfin-url", help="skip resolver; use this Redfin URL for the target home")
    ap.add_argument("--zillow-url", help="skip resolver; use this Zillow URL for the target home")
    ap.add_argument("--target-lat", type=float, help="skip lookup; supply target lat directly")
    ap.add_argument("--target-lng", type=float, help="skip lookup; supply target lng directly")
    ap.add_argument("--target-sqft", type=int)
    ap.add_argument("--target-beds", type=int)
    args = ap.parse_args(argv)

    target_override = None
    if args.target_lat is not None and args.target_lng is not None:
        target_override = {
            "address": args.address,
            "lat": args.target_lat, "lng": args.target_lng,
            "sqft": args.target_sqft, "beds": args.target_beds,
        }

    result = estimate_rent(
        args.address,
        radius_miles=args.radius_miles,
        max_radius_miles=args.max_radius_miles,
        target_comp_count=args.target_comp_count,
        beds_tolerance=args.beds_tolerance,
        redfin_url=args.redfin_url, zillow_url=args.zillow_url,
        target_override=target_override,
    )
    json.dump(result, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
