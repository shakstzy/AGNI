#!/usr/bin/env python3
"""Neighborhood / community research by ZIP -> demographics + crime.

Two free sources, each degrades gracefully:

  - Census ACS 5-year (by ZIP/ZCTA): median household income, poverty rate,
    percent renter-occupied, population, median gross rent. Needs a FREE Census
    API key (https://api.census.gov/data/key_signup.html) in $CENSUS_API_KEY;
    without it, demographics are skipped and flagged.

  - Crime (FBI UCR, city level) via OpenCrime's static JSON. No key. Needs the
    city + state; a ZIP with no resolvable city, or a city OpenCrime doesn't
    cover, skips crime (the ACS poverty rate is the soft proxy).

Schools are intentionally NOT here -- the cashflow dossier already pulls school
ratings from Redfin's listing data, which is the right source.

For Section 8 underwriting, the demographics matter: a high renter share with
moderate poverty signals strong, durable voucher demand.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from typing import Any

import _env

_ACS_YEAR = 2024  # latest released ACS 5-year as of mid-2026
_CENSUS_BASE = "https://api.census.gov/data/{year}/acs/acs5"
_OPENCRIME = "https://www.opencrime.us/data/cities/{slug}.json"
_IMPERSONATE = "chrome124"
_CENSUS_SENTINELS = {"-666666666", "-999999999", "-888888888", "-222222222", None, ""}

# Rough US reference rates (per 100k, FBI UCR) for above/below context.
_US_VIOLENT_PER_100K = 380.0
_US_PROPERTY_PER_100K = 1950.0

_ACS_VARS = {
    "median_hh_income": "B19013_001E",
    "_pov_total": "B17001_001E",
    "_pov_below": "B17001_002E",
    "_tenure_total": "B25003_001E",
    "_renter": "B25003_003E",
    "total_population": "B01003_001E",
    "median_gross_rent": "B25064_001E",
}

STATE_NAMES = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "DC": "District of Columbia",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "ME": "Maine",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MS": "Mississippi",
    "MO": "Missouri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NY": "New York",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "West Virginia",
    "WI": "Wisconsin",
    "WY": "Wyoming",
}


def _to_int(v: Any) -> int | None:
    if v is None or str(v) in _CENSUS_SENTINELS:
        return None
    try:
        return int(round(float(v)))
    except (TypeError, ValueError):
        return None


def _slugify(city: str, state_full: str) -> str:
    s = f"{city} {state_full}".lower()
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def _acs(zip_code: str, key: str, year: int) -> dict[str, Any] | None:
    from curl_cffi import requests as curl_requests

    params = {
        "get": ",".join(_ACS_VARS.values()),
        "for": f"zip code tabulation area:{zip_code}",
        "key": key,
    }
    try:
        r = curl_requests.get(
            _CENSUS_BASE.format(year=year),
            params=params,
            impersonate=_IMPERSONATE,
            timeout=30,
        )
    except Exception:
        return None
    if r.status_code != 200:
        return None
    try:
        payload = r.json()
    except ValueError:
        return None
    if not isinstance(payload, list) or len(payload) < 2:
        return None
    row = dict(zip(payload[0], payload[1]))

    pov_total = _to_int(row.get(_ACS_VARS["_pov_total"]))
    pov_below = _to_int(row.get(_ACS_VARS["_pov_below"]))
    tenure_total = _to_int(row.get(_ACS_VARS["_tenure_total"]))
    renter = _to_int(row.get(_ACS_VARS["_renter"]))
    return {
        "median_hh_income": _to_int(row.get(_ACS_VARS["median_hh_income"])),
        "poverty_rate": round(pov_below / pov_total, 4)
        if pov_total and pov_below is not None
        else None,
        "pct_renter": round(renter / tenure_total, 4)
        if tenure_total and renter is not None
        else None,
        "total_population": _to_int(row.get(_ACS_VARS["total_population"])),
        "median_gross_rent": _to_int(row.get(_ACS_VARS["median_gross_rent"])),
        "acs_year": year,
    }


def _crime(city: str, state_abbr: str, year: int = _ACS_YEAR) -> dict[str, Any] | None:
    state_full = STATE_NAMES.get((state_abbr or "").upper())
    if not city or not state_full:
        return None
    from curl_cffi import requests as curl_requests

    slug = _slugify(city, state_full)
    try:
        r = curl_requests.get(
            _OPENCRIME.format(slug=slug), impersonate=_IMPERSONATE, timeout=15
        )
    except Exception:
        return None
    if r.status_code != 200:
        return None
    try:
        data = r.json()
    except ValueError:
        return None
    years = data.get("years") or {}
    if not years:
        return None
    yr_key = str(year) if str(year) in years else max(years, key=lambda y: int(y))
    yr = years.get(yr_key) or {}
    violent = yr.get("violentRate")
    prop = yr.get("propertyRate")
    if violent is None and prop is None:
        return None
    return {
        "city": data.get("city") or city,
        "state": data.get("state") or state_abbr,
        "violent_rate_per_100k": violent,
        "property_rate_per_100k": prop,
        "murder_rate_per_100k": yr.get("murderRate"),
        "source_year": int(yr_key),
        "source": "opencrime.us / FBI UCR",
    }


def lookup(
    zip_code: str,
    *,
    city: str | None = None,
    state: str | None = None,
    census_key: str | None = None,
    acs_year: int = _ACS_YEAR,
) -> dict[str, Any]:
    zip_code = re.sub(r"\D", "", str(zip_code)).zfill(5)[:5]
    flags: list[str] = []
    _env.ensure_loaded()
    census_key = census_key or os.environ.get("CENSUS_API_KEY")

    acs = None
    if census_key:
        acs = _acs(zip_code, census_key, acs_year)
        if acs is None:
            flags.append(
                f"ACS demographics unavailable for ZIP {zip_code} "
                "(no ZCTA match, or Census API error)"
            )
    else:
        flags.append(
            "ACS demographics skipped: set a free CENSUS_API_KEY "
            "(https://api.census.gov/data/key_signup.html)"
        )

    crime = _crime(city, state, acs_year) if (city and state) else None
    if crime is None:
        if city and state:
            flags.append(
                f"Crime data unavailable for {city}, {state} "
                "(not in OpenCrime's city set); use ACS poverty rate as a soft proxy"
            )
        else:
            flags.append(
                "Crime data skipped: city/state not resolved (pass a full address)"
            )

    return {
        "ok": acs is not None or crime is not None,
        "zip": zip_code,
        "city": city,
        "state": state,
        "acs": acs,
        "crime": crime,
        "flags": flags,
    }


def _money(v: Any) -> str:
    return f"${v:,.0f}" if isinstance(v, (int, float)) else "—"


def _pct(v: Any) -> str:
    return f"{v * 100:.0f}%" if isinstance(v, (int, float)) else "—"


def _vs_us(rate: Any, us: float) -> str:
    if not isinstance(rate, (int, float)) or not us:
        return ""
    ratio = rate / us
    if ratio >= 1.25:
        return f" (≈{ratio:.1f}x US avg)"
    if ratio <= 0.8:
        return f" (≈{ratio:.1f}x US avg)"
    return " (≈US avg)"


def render_markdown(res: dict[str, Any]) -> str:
    """Render the neighborhood dossier section body (no `## heading`)."""
    out: list[str] = []
    acs = res.get("acs")
    if acs:
        bits = [
            f"median household income {_money(acs.get('median_hh_income'))}",
            f"poverty rate {_pct(acs.get('poverty_rate'))}",
            f"renter-occupied {_pct(acs.get('pct_renter'))}",
            f"median gross rent {_money(acs.get('median_gross_rent'))}/mo",
        ]
        pop = acs.get("total_population")
        pop_str = f"{pop:,}" if isinstance(pop, int) else "—"
        out.append(
            f"**Demographics (Census ACS {acs.get('acs_year')}, ZIP {res.get('zip')}).** "
            + ", ".join(bits)
            + f". Population {pop_str}."
        )
        if isinstance(acs.get("pct_renter"), (int, float)) and isinstance(
            acs.get("poverty_rate"), (int, float)
        ):
            if acs["pct_renter"] >= 0.4:
                out.append(
                    "_High renter share signals durable rental / voucher demand._"
                )
    else:
        out.append(
            "**Demographics.** Unavailable — set a free `CENSUS_API_KEY` to populate "
            "income, poverty, renter share, and median rent."
        )

    crime = res.get("crime")
    if crime:
        v = crime.get("violent_rate_per_100k")
        p = crime.get("property_rate_per_100k")
        out.append(
            f"**Crime ({crime.get('city')}, {crime.get('state')}, "
            f"FBI UCR {crime.get('source_year')}).** "
            f"Violent {v}/100k{_vs_us(v, _US_VIOLENT_PER_100K)}; "
            f"property {p}/100k{_vs_us(p, _US_PROPERTY_PER_100K)}."
        )
    else:
        out.append(
            "**Crime.** Unavailable at this granularity; the ACS poverty rate above "
            "is the soft safety proxy."
        )
    return "\n\n".join(out) + "\n"


def _resolve_and_lookup(
    address: str,
    *,
    zip_code: str | None,
    city: str | None,
    state: str | None,
    census_key: str | None,
    acs_year: int,
) -> dict[str, Any]:
    if (
        zip_code is None or city is None or state is None
    ) and not address.strip().isdigit():
        import lookup as _lookup

        agg = (_lookup.lookup(address).get("aggregate")) or {}
        zip_code = zip_code or agg.get("zip")
        city = city or agg.get("city")
        state = state or agg.get("state")
    if zip_code is None and address.strip().isdigit():
        zip_code = address.strip()
    if zip_code is None:
        return {"ok": False, "error": "could not resolve a ZIP; pass --zip"}
    res = lookup(
        zip_code, city=city, state=state, census_key=census_key, acs_year=acs_year
    )
    res["address"] = address
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="neighborhood", description="ZIP demographics + crime"
    )
    ap.add_argument(
        "address", help="address (resolved for ZIP/city/state) or a 5-digit ZIP"
    )
    ap.add_argument("--zip", dest="zip_code", help="skip lookup; use this ZIP")
    ap.add_argument("--city", help="city (for crime lookup)")
    ap.add_argument("--state", help="2-letter state (for crime lookup)")
    ap.add_argument("--census-key", help="Census API key (else $CENSUS_API_KEY)")
    ap.add_argument("--acs-year", type=int, default=_ACS_YEAR)
    ap.add_argument(
        "--markdown",
        action="store_true",
        help="also print the rendered markdown section",
    )
    args = ap.parse_args(argv)

    res = _resolve_and_lookup(
        args.address,
        zip_code=args.zip_code,
        city=args.city,
        state=args.state,
        census_key=args.census_key,
        acs_year=args.acs_year,
    )
    json.dump(res, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")
    if args.markdown and res.get("ok"):
        sys.stdout.write("\n" + render_markdown(res))


if __name__ == "__main__":
    main()
