"""Pro-forma cash flow for a single property (or duplex / multi-unit).

Writes ONE canonical markdown file per property at:
    $REAL_ESTATE_PROPERTIES_DIR/<slug>.md    (if env var set)
    --output-dir/<slug>.md                    (if CLI flag passed)
    ~/CORTANA/workspaces/real-estate/wiki/entities/properties/<slug>.md  (default)

Slug = address kebab-case. Address-or-URL on the CLI gets normalized
to the same slug as a prior run, so `re cashflow "<addr>"` is idempotent.

Frontmatter holds every input (property facts + assumptions). Body has
four owned sections that recompute on every run:
  - Cash flow            (stabilized + year-1 warranty side-by-side)
  - Pro forma detail     (monthly line items)
  - Assumptions          (each input + WHY this is the default)
  - Inputs used          (every number this run consumed)

Hand-authored sections (Pipeline notes, Backlinks, free-form `## Financing`,
`## Call notes`, anything else under headings we don't own) are preserved
verbatim across re-runs.

Defaults (Central TX investor):
    down              0.20    20% down
    rate              0.07    7.0% 30yr fixed
    term              30      years
    closing           0.03    3% of price
    vacancy           0.08
    pm                0.04
    maintenance       0.05
    capex             0.05
    insurance_rate    0.005   annual, % of price
    warranty_offset   0.60    year-1 maintenance reduction under builder warranty
    property_tax      0.021   Central TX bench (Austin + Travis + AISD)
"""

from __future__ import annotations

import datetime as _dt
import os
import re
from typing import Any

import lookup
import rent_estimate


def _default_properties_dir() -> str:
    env = os.environ.get("REAL_ESTATE_PROPERTIES_DIR")
    if env:
        return os.path.expanduser(env)
    return os.path.expanduser(
        "/home/shakstzy/HADES/workspaces/real-estate/wiki/entities/properties"
    )


def slugify_address(address: str) -> str:
    s = address.lower().strip()
    s = re.sub(r"https?://[^\s]+", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "unknown"


_FM_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)

_STRING_KEYS = frozenset(
    {
        "slug",
        "type",
        "address",
        "city",
        "state",
        "zip",
        "status",
        "purpose",
        "acquired_at",
        "last_touched",
        "zillow_url",
        "redfin_url",
        "rent_triangulation_verdict",
        "dscr_tier",
        "parcel_apn",
        "parcel_zoning",
        "parcel_lot_position",
        "parcel_backs_to",
    }
)


def _parse_value(raw: str, *, force_string: bool = False) -> Any:
    raw = raw.strip()
    if raw == "" or raw == "null" or raw == "~":
        return None
    if (raw.startswith('"') and raw.endswith('"')) or (
        raw.startswith("'") and raw.endswith("'")
    ):
        return raw[1:-1]
    if force_string:
        return raw
    if raw == "true":
        return True
    if raw == "false":
        return False
    try:
        if "." in raw or "e" in raw or "E" in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        return raw


def _format_value(v: Any, *, force_string: bool = False) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if force_string:
        s = str(v)
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if isinstance(v, (int, float)):
        return repr(v)
    s = str(v)
    if (
        any(ch in s for ch in [":", "#", "&", "*", "!", "|", ">", "%", "@", "`"])
        or s.strip() != s
    ):
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return s


def _strip_inline_comment(v: str) -> str:
    in_single = False
    in_double = False
    for i, ch in enumerate(v):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double:
            if i == 0 or v[i - 1].isspace():
                return v[:i].rstrip()
    return v


def _parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    m = _FM_RE.match(text)
    if not m:
        return {}, text
    body = text[m.end() :]
    fm: dict[str, Any] = {}
    for line in m.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        key = k.strip().lower()
        v_clean = _strip_inline_comment(v)
        fm[key] = _parse_value(v_clean, force_string=key in _STRING_KEYS)
    return fm, body


def _emit_frontmatter(fm: dict[str, Any]) -> str:
    section_order = [
        "# identity",
        ["slug", "type", "address", "city", "state", "zip"],
        "# status",
        ["status", "purpose", "acquired_at", "last_touched"],
        "# property facts",
        [
            "price",
            "sqft",
            "units",
            "property_type",
            "year_built",
            "property_tax_rate",
            "hoa_monthly",
            "annual_insurance",
            "zillow_url",
            "redfin_url",
        ],
        "# rent (zillow bbox comps + redfin triangulation)",
        [
            "rent_total_monthly",
            "rent_per_unit_monthly",
            "rent_comp_count",
            "rent_comp_count_met_target",
            "radius_miles",
            "max_radius_miles",
            "rent_radius_miles_used",
            "target_comp_count",
            "beds_tolerance",
            "redfin_rent_estimate",
            "rent_triangulation_verdict",
            "rent_spread_pct",
        ],
        "# loan assumptions",
        [
            "down_pct",
            "interest_rate",
            "term_years",
            "closing_pct",
        ],
        "# operating assumptions",
        [
            "vacancy_pct",
            "pm_pct",
            "maintenance_pct",
            "capex_pct",
            "insurance_annual_rate",
            "warranty_maintenance_offset_year_1",
        ],
    ]
    seen: set[str] = set()
    out: list[str] = ["---"]
    for entry in section_order:
        if isinstance(entry, str):
            out.append(entry)
        else:
            for k in entry:
                if k in fm:
                    out.append(
                        f"{k}: {_format_value(fm[k], force_string=k in _STRING_KEYS)}"
                    )
                    seen.add(k)
    leftover = [k for k in fm.keys() if k not in seen]
    if leftover:
        out.append("# extra")
        for k in leftover:
            out.append(f"{k}: {_format_value(fm[k], force_string=k in _STRING_KEYS)}")
    out.append("---")
    return "\n".join(out) + "\n"


_OWNED_SECTIONS = (
    "Cash flow",
    "DSCR financing",
    "Parcel intelligence",
    "Downside & risk",
    "Pro forma detail",
    "Property & neighborhood",
    "Section 8 voucher",
    "Neighborhood research",
    "Assumptions",
    "Inputs used",
)
_TRAILING_SECTIONS = ("Backlinks",)


def _split_sections(body: str) -> list[tuple[str | None, str]]:
    parts: list[tuple[str | None, str]] = []
    cur_heading: str | None = None
    cur_lines: list[str] = []
    in_fence = False
    fence_char: str | None = None
    for line in body.splitlines(keepends=True):
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            this_fence = "`" if stripped.startswith("```") else "~"
            if not in_fence:
                in_fence = True
                fence_char = this_fence
            elif fence_char == this_fence:
                in_fence = False
                fence_char = None
            cur_lines.append(line)
            continue
        if not in_fence:
            m = re.match(r"^##\s+(.*?)\s*$", line.rstrip("\n"))
            if m:
                if cur_lines or cur_heading is not None:
                    parts.append((cur_heading, "".join(cur_lines)))
                cur_heading = m.group(1).strip()
                cur_lines = []
                continue
        cur_lines.append(line)
    parts.append((cur_heading, "".join(cur_lines)))
    return parts


def _stitch_sections(
    intro: str, owned: dict[str, str], non_owned_in_order: list[tuple[str, str]]
) -> str:
    out: list[str] = []
    if intro.strip():
        out.append(intro.rstrip() + "\n\n")
    for h in _OWNED_SECTIONS:
        if h in owned:
            out.append(f"## {h}\n\n{owned[h].rstrip()}\n\n")
    trailing: list[tuple[str, str]] = []
    for h, content in non_owned_in_order:
        if h in _TRAILING_SECTIONS:
            trailing.append((h, content))
        else:
            out.append(f"## {h}\n\n{content.rstrip()}\n\n")
    for h, content in trailing:
        out.append(f"## {h}\n\n{content.rstrip()}\n\n")
    return "".join(out).rstrip() + "\n"


def _monthly_pi(loan: float, annual_rate: float, term_years: int) -> float:
    if loan <= 0:
        return 0.0
    mr = annual_rate / 12.0
    n = term_years * 12
    if mr == 0:
        return loan / n
    return loan * (mr * (1 + mr) ** n) / ((1 + mr) ** n - 1)


def _scenario(
    *,
    gross_rent_monthly: float,
    monthly_pi: float,
    prop_tax_monthly: float,
    insurance_monthly: float,
    hoa_monthly: float,
    vacancy_pct: float,
    pm_pct: float,
    maintenance_pct: float,
    capex_pct: float,
    utilities_pct: float = 0.0,
    opex_floor_pct: float = 0.0,
) -> dict:
    variable_pct = vacancy_pct + pm_pct + maintenance_pct + capex_pct + utilities_pct
    vacancy = gross_rent_monthly * vacancy_pct
    pm = gross_rent_monthly * pm_pct
    maintenance = gross_rent_monthly * maintenance_pct
    capex = gross_rent_monthly * capex_pct
    utilities = gross_rent_monthly * utilities_pct
    fixed = prop_tax_monthly + insurance_monthly + hoa_monthly
    operating = vacancy + pm + maintenance + capex + utilities + fixed
    # "50% rule" backstop: cheap class-C rentals realistically run operating
    # expenses (everything except debt service) at ~50% of gross. If the itemized
    # stack lands below the floor, use the floor -- it's the single most reliable
    # guard against fantasy cash flow (adversarial review 2026-06).
    floor = gross_rent_monthly * opex_floor_pct
    opex_floor_applied = operating < floor
    if opex_floor_applied:
        operating = floor
    noi_monthly = gross_rent_monthly - operating
    cash_flow_monthly = noi_monthly - monthly_pi
    breakeven = (monthly_pi + fixed) / (1 - variable_pct) if variable_pct < 1 else None
    return {
        "gross_rent_monthly": round(gross_rent_monthly, 2),
        "vacancy_monthly": round(vacancy, 2),
        "pm_monthly": round(pm, 2),
        "maintenance_monthly": round(maintenance, 2),
        "capex_monthly": round(capex, 2),
        "utilities_monthly": round(utilities, 2),
        "prop_tax_monthly": round(prop_tax_monthly, 2),
        "insurance_monthly": round(insurance_monthly, 2),
        "hoa_monthly": round(hoa_monthly, 2),
        "operating_expenses_monthly": round(operating, 2),
        "opex_floor_applied": opex_floor_applied,
        "noi_monthly": round(noi_monthly, 2),
        "noi_annual": round(noi_monthly * 12, 2),
        "monthly_pi": round(monthly_pi, 2),
        "cash_flow_monthly": round(cash_flow_monthly, 2),
        "cash_flow_annual": round(cash_flow_monthly * 12, 2),
        "breakeven_rent_monthly": round(breakeven, 2) if breakeven else None,
    }


def _downside(stab: dict, base: dict, fm: dict, units: int) -> dict:
    """Adversarial worst-case + the risk metrics the realistic pro forma hides.

    Returns a worst-case scenario (chronic vacancy + softer rent + a hotter
    expense year), a break-even occupancy, the cash flow with one whole unit
    vacant (small-MF concentration risk), a recommended reserve, and a plain-
    English risk register for the costs/risks not in the monthly model."""
    gross = stab["gross_rent_monthly"]
    debt = stab["monthly_pi"]
    price = float(fm["price"])
    loan = price * (1 - float(fm["down_pct"]))

    # Carry cost that exists regardless of occupancy = operating minus the vacancy
    # line (occupancy is the variable we solve for), plus debt service.
    carry = (stab["operating_expenses_monthly"] - stab["vacancy_monthly"]) + debt
    break_even_occ = round(carry / gross, 3) if gross else None

    # One whole unit vacant all year: collect the other units' rent, still pay the
    # occupancy-independent carry. The concrete "super vacant" case for a duplex.
    occ_units = max(units - 1, 0)
    one_vacant_gross = gross * (occ_units / units) if units else gross
    one_unit_vacant_cf = round(one_vacant_gross - carry, 2)

    # Worst-case scenario: stress rent down, vacancy up, expense floor up.
    stress_gross = gross * (1 - float(fm.get("stress_rent_haircut") or 0.0))
    worst = _scenario(
        gross_rent_monthly=stress_gross,
        monthly_pi=debt,
        prop_tax_monthly=base["prop_tax_monthly"],
        insurance_monthly=base["insurance_monthly"],
        hoa_monthly=base["hoa_monthly"],
        vacancy_pct=float(fm.get("stress_vacancy_pct") or 0.25),
        pm_pct=base["pm_pct"],
        maintenance_pct=fm["maintenance_pct"] * 1.5,  # bad-year repair load
        capex_pct=base["capex_pct"],
        utilities_pct=base.get("utilities_pct") or 0.0,
        opex_floor_pct=float(fm.get("stress_opex_floor_pct") or 0.55),
    )
    worst_cf = worst["cash_flow_monthly"]
    # Reserve to survive: a year of worst-case burn (if negative) + one capital event.
    annual_burn = max(0.0, -worst_cf) * 12
    reserve = round(annual_burn + 10000)

    risks: list[str] = []
    if units and units <= 2:
        risks.append(
            f"CONCENTRATION: {round(100 / units)}% of income is one unit — a single "
            f"vacancy turns cash flow to ${one_unit_vacant_cf:,.0f}/mo."
        )
    if loan < 75000:
        risks.append(
            f"FINANCING: a ~${loan:,.0f} loan is under most lenders' small-balance "
            f"floor; expect higher rate, 25%+ down, or all-cash — the 20%/7% base is "
            f"optimistic."
        )
    if break_even_occ is not None and break_even_occ > 0.90:
        risks.append(
            f"FRAGILE: needs {break_even_occ * 100:.0f}% occupancy just to break even."
        )
    risks.append(
        "LEAD-SAFE: pre-1978 Cleveland rentals (nearly all this stock) need a Lead "
        "Safe certificate to license — remediation can run thousands and blocks renting."
    )
    risks.append(
        "CAPITAL EVENTS: roof/furnace/sewer/foundation run $8-20k and aren't in "
        "monthly capex — one event can erase a year+ of cash flow."
    )
    risks.append(
        "CONDITION UNSEEN: listing photos hide deferred maintenance; a real inspection "
        "+ rehab quote must clear before committing (the rehab reserve is a guess)."
    )
    return {
        "worst_case": worst,
        "break_even_occupancy": break_even_occ,
        "one_unit_vacant_cash_flow_monthly": one_unit_vacant_cf,
        "reserve_recommended": reserve,
        "risk_register": risks,
    }


DEFAULTS: dict[str, Any] = {
    "down_pct": 0.20,
    "interest_rate": 0.07,
    "term_years": 30,
    "closing_pct": 0.03,
    # Operating-expense defaults tuned for cheap class-C/D rentals (80-100yr
    # Rust-Belt stock, out-of-state), NOT class-B suburban. Adversarial review
    # (2026-06): the old 8/4/5/5 stack modeled ~25% OpEx vs the 50%+ reality.
    "vacancy_pct": 0.10,  # class-C turnover + eviction downtime
    "pm_pct": 0.10,  # real small-MF, out-of-state management (4% was fiction)
    "maintenance_pct": 0.08,  # old stock, frequent repairs
    "capex_pct": 0.08,  # roof/furnace/sewer reserve on aged systems
    "utilities_pct": 0.05,  # landlord-paid water/sewer/trash common on old stock
    "opex_floor_pct": 0.50,  # the "50% rule" as a hard backstop on operating exp
    "rent_haircut_pct": 0.10,  # discount the optimistic comp/Rent-Zestimate rent
    "rehab_per_unit": 0,  # upfront make-ready into cash invested (set per market)
    "effective_tax_rate": None,  # when set: tax = price x rate (reassessment-on-sale)
    "insurance_annual_rate": 0.007,  # distressed-area rates run higher
    # Adversarial worst-case knobs (the downside scenario, alongside the realistic
    # one): a bad year with chronic vacancy, softer rent, and a hotter expense run.
    "stress_vacancy_pct": 0.25,  # a unit sits empty / heavy turnover
    "stress_rent_haircut": 0.10,  # rent another 10% under the conservative estimate
    "stress_opex_floor_pct": 0.55,  # bad years run above the 50% baseline
    "warranty_maintenance_offset_year_1": 0.60,
    "units": 1,
}


# Effective property-tax bench by state for the fallback path (used only
# when Zillow doesn't return property_tax_rate). These are county-mix
# benches, not exact — always override with the parcel-specific rate when
# possible. Source: Tax Foundation effective tax rate by state, latest.
_STATE_TAX_DEFAULT: dict[str, float] = {
    "AL": 0.0041,
    "AK": 0.0119,
    "AZ": 0.0066,
    "AR": 0.0064,
    "CA": 0.0075,
    "CO": 0.0055,
    "CT": 0.0204,
    "DE": 0.0058,
    "FL": 0.0089,
    "GA": 0.0092,
    "HI": 0.0029,
    "ID": 0.0069,
    "IL": 0.0227,
    "IN": 0.0085,
    "IA": 0.0157,
    "KS": 0.0141,
    "KY": 0.0086,
    "LA": 0.0056,
    "ME": 0.0136,
    "MD": 0.0109,
    "MA": 0.0123,
    "MI": 0.0154,
    "MN": 0.0112,
    "MS": 0.0081,
    "MO": 0.0097,
    "MT": 0.0084,
    "NE": 0.0167,
    "NV": 0.0059,
    "NH": 0.0218,
    "NJ": 0.0249,
    "NM": 0.0080,
    "NY": 0.0173,
    "NC": 0.0082,
    "ND": 0.0098,
    "OH": 0.0156,
    "OK": 0.0090,
    "OR": 0.0093,
    "PA": 0.0149,
    "RI": 0.0153,
    "SC": 0.0057,
    "SD": 0.0124,
    "TN": 0.0071,
    "TX": 0.0210,
    "UT": 0.0066,
    "VT": 0.0190,
    "VA": 0.0082,
    "WA": 0.0098,
    "WV": 0.0058,
    "WI": 0.0185,
    "WY": 0.0061,
    "DC": 0.0062,
}


# Plain-English rationale for each default, surfaced into the property .md so
# anyone reading later (including future Adithya) sees WHERE each number came
# from. Edit a value in frontmatter and the table updates with that value; the
# rationale stays as the why.
_ASSUMPTION_RATIONALE: dict[str, tuple[str, str]] = {
    "down_pct": (
        "Down payment",
        "20% is the conventional non-owner-occupied minimum (Fannie/Freddie). "
        "Below 20% means a second-home loan instead, which requires intent-to-occupy and "
        "is fraud-flagged on rentals.",
    ),
    "interest_rate": (
        "Mortgage rate",
        "7.0% is a TX 30yr fixed bench for non-owner-occupied as of writing. "
        "Override --rate with a real quote when you have one — investor loans run "
        "0.25-0.5% above primary-residence rates.",
    ),
    "term_years": (
        "Loan term",
        "30yr fixed is standard for buy-and-hold. 15yr cuts cash flow in half for the "
        "first decade in exchange for finishing the loan ~10yr earlier.",
    ),
    "closing_pct": (
        "Closing costs (% of price, paid up front)",
        "3% covers TX title insurance + escrow + recording + lender origination. "
        "TX has no real-estate transfer tax. New-construction closings typically "
        "negotiate the builder to cover this; subtract it then.",
    ),
    "vacancy_pct": (
        "Vacancy reserve",
        "8% = roughly one month per year offline. Central-TX SFHs in good zips hit "
        "5-6% in practice; deeper-suburb or older-comp homes run 10-12%.",
    ),
    "pm_pct": (
        "Property management",
        "4% is the floor for self-managed plus the inevitable handyman/tenant-comms "
        "overhead. Full-service PM runs 8-10% of gross rent — bump this when handing "
        "off to a third party.",
    ),
    "maintenance_pct": (
        "Maintenance reserve",
        "5% of gross rent for normal wear-and-tear (HVAC service, paint touch-ups, "
        "appliance repair). Year-1 typically lower under a builder warranty — see "
        "warranty_maintenance_offset_year_1 below.",
    ),
    "capex_pct": (
        "Capital expenditure reserve",
        "5% of rent puts aside cash for big-ticket replacements over their useful "
        "life: roof 25yr, HVAC 15yr, water heater 10yr, appliances 8-12yr. New-builds "
        "feel like they don't need this; year 8+ proves otherwise.",
    ),
    "insurance_annual_rate": (
        "Insurance (% of price / year)",
        "0.5% annual is a TX HO3 landlord-policy bench. Coastal TX, wildfire-zone, "
        "or properties with prior claims run 0.8-1.5%. When the property's actual "
        "annual premium is known, set annual_insurance directly and this rate is "
        "ignored.",
    ),
    "warranty_maintenance_offset_year_1": (
        "Builder warranty maintenance offset (year 1)",
        "60% reduction to maintenance in year 1 of a new build, when the builder "
        "warranty covers structural + appliances + workmanship. Set to 0 for any "
        "resale property — there is no warranty to lean on.",
    ),
    "property_tax_rate": (
        "Property tax rate",
        "A state effective-rate bench (the table covers all 50 states + DC); the "
        "value shown is for this property's state. Always replace with the "
        "parcel-specific rate once you have it — US effective rates run ~0.3-2.5% "
        "and the local stack varies widely inside one metro. A listing-derived rate "
        "above 5% is treated as a parse error and replaced with this bench.",
    ),
}


def _hydrate_property_facts(
    fm: dict[str, Any], cli: dict[str, Any], pre_lookup: dict[str, Any] | None
) -> tuple[dict[str, Any], list[str]]:
    flags: list[str] = []
    facts: dict[str, Any] = {}
    needed = [
        "price",
        "sqft",
        "property_tax_rate",
        "hoa_monthly",
        "annual_insurance",
        "year_built",
        "zillow_url",
        "redfin_url",
        "city",
        "state",
        "zip",
    ]

    for k in needed:
        if k in cli and cli[k] is not None:
            facts[k] = cli[k]
        elif k in fm and fm[k] is not None:
            facts[k] = fm[k]

    if pre_lookup is not None:
        agg = pre_lookup.get("aggregate") or {}
        if facts.get("price") is None:
            # Zillow occasionally returns price=$1 / $1000 / similar on sold
            # or off-market listings (probably a rental-listing field bleeding
            # through). Anything under $20k for a US property is a data
            # error — fall back to zestimate and flag.
            raw_price = agg.get("price")
            zest = agg.get("zestimate")
            if raw_price is not None and raw_price < 20000:
                if zest is not None and zest >= 20000:
                    facts["price"] = zest
                    flags.append(
                        f"price ${raw_price:,.0f} looked like a data error; "
                        f"using zestimate ${zest:,.0f} instead. Override with --price."
                    )
                else:
                    facts["price"] = raw_price
                    flags.append(
                        f"both price ${raw_price:,.0f} and zestimate look invalid; "
                        f"pass --price <amount> to override."
                    )
            else:
                facts["price"] = raw_price or zest
        if facts.get("sqft") is None:
            facts["sqft"] = agg.get("sqft")
        if facts.get("days_on_market") is None:
            facts["days_on_market"] = agg.get("days_on_market")
        # --- Per-listing property tax (Change 1) ---
        # Prefer the parsed annual tax dollar amount when available. Derive a
        # per-parcel rate from it (annual_tax / price) rather than using the
        # aggregate-level property_tax_rate, which may be a state/county average.
        annual_tax_raw = agg.get("annual_property_tax")
        if annual_tax_raw is not None and isinstance(annual_tax_raw, (int, float)):
            facts["annual_property_tax"] = round(float(annual_tax_raw), 2)
            facts["_property_tax_source"] = "listing"  # per-parcel
        if facts.get("property_tax_rate") is None:
            if (
                facts.get("annual_property_tax") is not None
                and facts.get("price") is not None
            ):
                try:
                    price_f = float(facts["price"])
                    if price_f > 0:
                        derived = facts["annual_property_tax"] / price_f
                        facts["property_tax_rate"] = round(derived, 6)
                except (TypeError, ValueError):
                    pass
            if facts.get("property_tax_rate") is None:
                ptr = agg.get("property_tax_rate")
                if ptr is not None:
                    facts["property_tax_rate"] = round(
                        ptr / 100.0 if ptr > 1 else ptr, 6
                    )
        if facts.get("hoa_monthly") is None:
            facts["hoa_monthly"] = agg.get("monthly_hoa_fee")
        if facts.get("annual_insurance") is None:
            facts["annual_insurance"] = agg.get("annual_homeowners_insurance")
        if facts.get("year_built") is None:
            facts["year_built"] = agg.get("year_built")
        if facts.get("zillow_url") is None:
            facts["zillow_url"] = pre_lookup.get("zillow_url")
        if facts.get("redfin_url") is None:
            facts["redfin_url"] = pre_lookup.get("redfin_url")
        for k in ("city", "state", "zip"):
            if facts.get(k) is None and agg.get(k) is not None:
                facts[k] = str(agg.get(k))

    ptr = facts.get("property_tax_rate")
    if ptr is not None and ptr > 0.05:
        flags.append(
            f"property_tax_rate {ptr * 100:.1f}% from the listing is implausible (>5%); "
            "discarded as a parse error -- using the state bench instead."
        )
        facts["property_tax_rate"] = None
        facts.pop("_property_tax_source", None)
        facts.pop("annual_property_tax", None)

    if facts.get("property_tax_rate") is None:
        state = (facts.get("state") or "").upper()
        rate = _STATE_TAX_DEFAULT.get(state, 0.015)
        facts["property_tax_rate"] = rate
        facts.setdefault("_property_tax_source", "state_bench")
        if state in _STATE_TAX_DEFAULT:
            flags.append(
                f"property_tax_rate fell back to {state} bench ({rate * 100:.2f}%). "
                f"Override with --property-tax-rate for the parcel-specific rate."
            )
        else:
            flags.append(
                f"property_tax_rate fell back to generic US 1.5% (state {state!r} "
                f"not in bench table). Override with --property-tax-rate."
            )
    else:
        facts.setdefault("_property_tax_source", "listing")
    if facts.get("hoa_monthly") is None:
        facts["hoa_monthly"] = 0.0

    return facts, flags


def _hydrate_rent(
    address: str,
    fm: dict[str, Any],
    cli: dict[str, Any],
    units: int,
    *,
    radius_miles: float,
    beds_tolerance: int,
    max_radius_miles: float,
    target_comp_count: int,
    zillow_url: str | None,
    redfin_url: str | None,
    pre_lookup: dict[str, Any] | None,
) -> tuple[dict[str, Any], list[str], dict[str, Any]]:
    flags: list[str] = []
    rent: dict[str, Any] = {}
    est: dict[str, Any] = {}
    if cli.get("rent_total_monthly") is not None:
        rent["rent_total_monthly"] = cli["rent_total_monthly"]
    elif cli.get("rent_per_unit_monthly") is not None:
        rent["rent_per_unit_monthly"] = cli["rent_per_unit_monthly"]
        rent["rent_total_monthly"] = cli["rent_per_unit_monthly"] * units
    elif fm.get("rent_total_monthly") is not None:
        rent["rent_total_monthly"] = fm["rent_total_monthly"]
        rent.setdefault("rent_per_unit_monthly", fm.get("rent_per_unit_monthly"))
        if fm.get("rent_comp_count") is not None:
            rent["rent_comp_count"] = fm["rent_comp_count"]
    else:
        agg = (pre_lookup or {}).get("aggregate") or {}
        # For 2-4 unit buildings, estimate PER UNIT then multiply -- never the
        # whole building as one home. A duplex Redfin reports as "5 bd / 2224
        # sqft" must not match 5-bed single-family rentals; it rents as two
        # smaller units. Split beds + sqft across units for the comp search,
        # reusing the same per-unit bed count the Section 8 lookup uses.
        split = units > 1
        if split:
            per_unit_beds, _ = _beds_per_unit(fm, agg, units, cli)
            sqft = agg.get("sqft")
            per_unit_sqft = (
                round(sqft / units) if isinstance(sqft, (int, float)) and sqft else None
            )
        else:
            per_unit_beds, per_unit_sqft = agg.get("beds"), agg.get("sqft")
        target_override = None
        if agg.get("lat") is not None and agg.get("lng") is not None:
            target_override = {
                "address": address,
                "lat": agg.get("lat"),
                "lng": agg.get("lng"),
                "sqft": per_unit_sqft,
                "beds": per_unit_beds,
                "zip": agg.get("zip"),
            }
        est = rent_estimate.estimate_rent(
            address,
            radius_miles=radius_miles,
            max_radius_miles=max_radius_miles,
            target_comp_count=target_comp_count,
            beds_tolerance=beds_tolerance,
            redfin_url=redfin_url,
            zillow_url=zillow_url,
            target_override=target_override,
        )
        single = est.get("estimated_rent_mid")
        if single is None:
            # Fall back to HUD FY2026 Small Area FMR (SAFMR) for the target ZIP code & bedroom count
            zip_match = re.search(r"\b([A-Za-z]{2})\s+(\d{5})\b", address or "")
            target_zip = (
                agg.get("zip")
                or fm.get("zip")
                or (zip_match.group(2) if zip_match else None)
            )
            beds_val = per_unit_beds or cli.get("beds_per_unit") or (
                (agg.get("beds") // max(1, units)) if agg.get("beds") else 2
            )
            try:
                fmr_beds = min(4, max(0, int(beds_val)))
            except (ValueError, TypeError):
                fmr_beds = 2
            if target_zip:
                try:
                    import fmr

                    fmr_data = fmr.lookup(str(target_zip))
                    if fmr_data and fmr_data.get("ok") and fmr_data.get("fmr"):
                        fmr_rent = fmr_data["fmr"].get(fmr_beds) or fmr_data["fmr"].get(
                            str(fmr_beds)
                        )
                        if fmr_rent and float(fmr_rent) > 0:
                            single = float(fmr_rent)
                            flags.append(
                                f"rent estimate fell back to HUD FY2026 Small Area FMR for ZIP {target_zip} (${single:.0f}/mo for {fmr_beds}BR)"
                            )
                except Exception:
                    pass

        if single is None:
            return (
                {
                    "rent_total_monthly": None,
                    "rent_per_unit_monthly": None,
                    "rent_comp_count": est.get("comp_count", 0),
                },
                ["no rent comps; pass --rent-total or --rent-per-unit"],
                est,
            )
        cc = est.get("comp_count") or 0
        if cc < 5:
            flags.append(f"thin rent comps ({cc} matches)")
        # Underwriting haircut: comp / Rent-Zestimate numbers skew high for cheap
        # class-C multifamily (adversarial review 2026-06), so discount toward a
        # conservative, collectible rent before it drives the pro forma. Store the
        # raw estimate for transparency.
        haircut = cli.get("rent_haircut_pct")
        if haircut is None:
            haircut = DEFAULTS["rent_haircut_pct"]
        haircut = float(haircut)
        rent["rent_estimate_raw_mid"] = round(single)
        rent["rent_haircut_pct"] = haircut
        single = round(single * (1 - haircut))
        # `single` is the per-unit rent when we split across units; scale it back
        # up to the whole building.
        per_unit = split and target_override is not None
        total = single * units if per_unit else single
        if per_unit:
            rent["rent_per_unit_monthly"] = single
        rent["rent_total_monthly"] = total
        rent["rent_comp_count"] = cc
        rent["rent_radius_miles_used"] = est.get("radius_miles_used")
        rent["rent_comp_count_met_target"] = est.get("comp_count_met_target")
        rent["redfin_rent_estimate"] = est.get("redfin_rent_estimate")
        rent["rental_dom_median"] = est.get("rental_dom_median")
        # Triangulate against Redfin at the BUILDING level: Redfin's rent
        # estimate (when present) is whole-building, while our Zillow number is
        # per-unit x units, so compare the two building totals -- not per-unit.
        rf = est.get("redfin_rent_estimate")
        if isinstance(rf, (int, float)) and rf > 0:
            spread = abs(total - rf) / ((total + rf) / 2)
            rent["rent_spread_pct"] = round(spread * 100, 1)
            rent["rent_triangulation_verdict"] = (
                "strong" if spread <= 0.10 else "soft" if spread <= 0.25 else "diverged"
            )
            if spread > 0.25:
                flags.append(
                    f"rent triangulation DIVERGED: Zillow {total} vs Redfin "
                    f"{rf} ({rent['rent_spread_pct']}% spread)"
                )
        else:
            rent["rent_triangulation_verdict"] = est.get("triangulation_verdict")
            rent["rent_spread_pct"] = est.get("spread_pct")

    if (
        rent.get("rent_per_unit_monthly") is None
        and rent.get("rent_total_monthly") is not None
        and units
    ):
        rent["rent_per_unit_monthly"] = round(rent["rent_total_monthly"] / units, 2)
    return rent, flags, est


_RENT_BOLSTER_TAGS: list[tuple[str, str]] = [
    ("renovated", "renovated"),
    ("remodeled", "remodeled"),
    ("updated", "updated"),
    ("new roof", "new roof"),
    ("new furnace", "new furnace"),
    ("new hvac", "new hvac"),
    ("new windows", "new windows"),
    ("new kitchen", "new kitchen"),
    ("granite", "granite"),
    ("quartz", "quartz"),
    ("stainless", "stainless"),
    ("hardwood", "hardwood"),
    ("luxury vinyl", "lvp"),
    ("lvp", "lvp"),
    ("finished basement", "finished basement"),
    ("central air", "central air"),
    ("in-unit laundry", "in-unit laundry"),
    ("new appliances", "new appliances"),
    ("move-in ready", "move-in ready"),
    ("turnkey", "turnkey"),
]


def extract_rent_bolsters(text: str) -> list[str]:
    """Return deduped canonical rent-bolster tags found in text (case-insensitive).

    Scans for each phrase from _RENT_BOLSTER_TAGS and emits the canonical tag
    on a match.  Max 10 tags returned."""
    if not text:
        return []
    lower = text.lower()
    seen: set[str] = set()
    out: list[str] = []
    for phrase, canonical in _RENT_BOLSTER_TAGS:
        if canonical not in seen and phrase in lower:
            seen.add(canonical)
            out.append(canonical)
            if len(out) >= 10:
                break
    return out


def _money(v: Any) -> str:
    if not isinstance(v, (int, float)) or v is None:
        return "—"
    return f"${v:,.0f}"


def _pct(v: Any) -> str:
    if not isinstance(v, (int, float)) or v is None:
        return "—"
    return f"{v * 100:.2f}%"


def _render_cashflow(stab: dict, yr1: dict) -> str:
    return (
        "| Scenario | NOI / mo | Cash flow / mo | Cap rate | CoC | Breakeven rent / mo |\n"
        "|---|---|---|---|---|---|\n"
        f"| stabilized | {_money(stab.get('noi_monthly'))} | {_money(stab.get('cash_flow_monthly'))} "
        f"| {_pct(stab.get('cap_rate'))} | {_pct(stab.get('cash_on_cash'))} "
        f"| {_money(stab.get('breakeven_rent_monthly'))} |\n"
        f"| year 1 (warranty) | {_money(yr1.get('noi_monthly'))} | {_money(yr1.get('cash_flow_monthly'))} "
        f"| {_pct(yr1.get('cap_rate'))} | {_pct(yr1.get('cash_on_cash'))} "
        f"| {_money(yr1.get('breakeven_rent_monthly'))} |\n"
    )


def _render_downside(downside: dict, stab: dict) -> str:
    worst = downside.get("worst_case") or {}
    be = downside.get("break_even_occupancy")
    lines = [
        "Worst case stress-tests chronic vacancy (25%), rent another 10% under the "
        "(already conservative) estimate, and a hotter ~55%+ expense year:",
        "",
        "| Case | Cash flow / mo | Cap rate | Occupancy to break even |",
        "|---|---|---|---|",
        f"| realistic | {_money(stab.get('cash_flow_monthly'))} | {_pct(stab.get('cap_rate'))} "
        f"| {_pct(be) if be is not None else '—'} |",
        f"| **worst case** | {_money(worst.get('cash_flow_monthly'))} "
        f"| {_pct(worst.get('cap_rate'))} | — |",
        "",
        f"- **One unit vacant all year:** "
        f"{_money(downside.get('one_unit_vacant_cash_flow_monthly'))}/mo "
        "(small-MF concentration — half a duplex empty).",
        f"- **Reserve to survive a bad year + one capital event:** "
        f"{_money(downside.get('reserve_recommended'))}.",
        "",
        "**Major risks not in the monthly model:**",
    ]
    lines += [f"- {r}" for r in (downside.get("risk_register") or [])]
    return "\n".join(lines) + "\n"


def _render_pro_forma(stab: dict) -> str:
    rows = [
        ("Gross rent", stab.get("gross_rent_monthly")),
        ("− Vacancy", -1 * (stab.get("vacancy_monthly") or 0)),
        ("− Property mgmt", -1 * (stab.get("pm_monthly") or 0)),
        ("− Maintenance", -1 * (stab.get("maintenance_monthly") or 0)),
        ("− Capex reserve", -1 * (stab.get("capex_monthly") or 0)),
        ("− Utilities", -1 * (stab.get("utilities_monthly") or 0)),
        ("− Property tax", -1 * (stab.get("prop_tax_monthly") or 0)),
        ("− Insurance", -1 * (stab.get("insurance_monthly") or 0)),
        ("− HOA", -1 * (stab.get("hoa_monthly") or 0)),
        ("**= NOI**", stab.get("noi_monthly")),
        ("− Mortgage P+I", -1 * (stab.get("monthly_pi") or 0)),
        ("**= Cash flow**", stab.get("cash_flow_monthly")),
    ]
    out = ["| Line | Monthly |", "|---|---|"]
    for label, val in rows:
        out.append(f"| {label} | {_money(val)} |")
    return "\n".join(out) + "\n"


def _render_assumptions(fm: dict[str, Any]) -> str:
    """Render each loan / operating / tax assumption with its current value
    and the rationale for the default. Run-specific so the numbers always
    reflect what THIS run used, not what the rationale text was originally
    written against.
    """
    out: list[str] = [
        "Each number below was used in this analysis. The rationale explains why "
        "the default is what it is — override any field in frontmatter and re-run "
        "to swap in your own number.\n",
        "| Assumption | Value | Why this default |",
        "|---|---|---|",
    ]
    order = [
        "down_pct",
        "interest_rate",
        "term_years",
        "closing_pct",
        "vacancy_pct",
        "pm_pct",
        "maintenance_pct",
        "capex_pct",
        "insurance_annual_rate",
        "warranty_maintenance_offset_year_1",
        "property_tax_rate",
    ]
    for k in order:
        label, why = _ASSUMPTION_RATIONALE.get(k, (k, ""))
        v = fm.get(k)
        if k == "term_years":
            value_str = f"{int(v)} yr" if isinstance(v, (int, float)) else "—"
        elif isinstance(v, float) and 0 <= v <= 1:
            value_str = _pct(v)
        elif isinstance(v, (int, float)):
            value_str = _money(v)
        else:
            value_str = "—"
        out.append(f"| {label} | {value_str} | {why} |")
    # Rent source explanation
    rent_v = fm.get("rent_triangulation_verdict")
    rent_lines = ["", "**Rent estimate.**"]
    z_mid = fm.get("rent_total_monthly")
    rf_rent = fm.get("redfin_rent_estimate")
    spread = fm.get("rent_spread_pct")
    if fm.get("rent_comp_count") and z_mid is not None:
        radius_used = fm.get("rent_radius_miles_used") or fm.get("radius_miles")
        beds_tol = fm.get("beds_tolerance", 0)
        beds_clause = (
            "exact beds match" if beds_tol == 0 else f"±{beds_tol} beds tolerance"
        )
        target_n = fm.get("target_comp_count") or 40
        met = fm.get("rent_comp_count_met_target")
        meta = (
            ""
            if met is None
            else (
                " (target met)"
                if met
                else f" (target was {target_n}, only this many available)"
            )
        )
        rent_lines.append(
            f"Zillow bbox median across {fm.get('rent_comp_count')} comps{meta} in "
            f"{radius_used} mi auto-expanded from {fm.get('radius_miles')} mi, "
            f"{beds_clause}: {_money(z_mid)} / mo."
        )
    if rf_rent is not None:
        rent_lines.append(
            f"Redfin native RentalEstimate (independent number for triangulation): {_money(rf_rent)} / mo."
        )
    if rent_v == "strong":
        rent_lines.append(
            f"Triangulation: STRONG (Zillow vs Redfin within 10% — {spread}% spread). High-confidence rent."
        )
    elif rent_v == "soft":
        rent_lines.append(
            f"Triangulation: SOFT (Zillow vs Redfin within 25% but >10% — {spread}% spread). Used the lower of the two for conservatism."
        )
    elif rent_v == "diverged":
        rent_lines.append(
            f"Triangulation: DIVERGED (>25% spread between Zillow and Redfin — {spread}%). Cashflow used the Zillow comp median but hand-verify before committing."
        )
    elif rent_v == "single_zillow":
        rent_lines.append(
            "Triangulation: only Zillow-comp rent available (Redfin had no native rent estimate for this property, common for off-market)."
        )
    elif rent_v == "single_redfin":
        rent_lines.append(
            "Triangulation: only Redfin RentalEstimate available (Zillow comps below threshold)."
        )
    out.append("\n".join(rent_lines))
    return "\n".join(out) + "\n"


def _render_inputs_used(
    fm: dict[str, Any], total_cash_invested: float, loan: float, monthly_pi: float
) -> str:
    rows = [
        ("Price", _money(fm.get("price"))),
        ("Sqft", str(fm.get("sqft") or "—")),
        ("Units", str(fm.get("units") or 1)),
        ("Down pct", _pct(fm.get("down_pct"))),
        ("Interest rate", _pct(fm.get("interest_rate"))),
        ("Term", f"{fm.get('term_years')}yr"),
        ("Loan amount", _money(loan)),
        ("Monthly P+I", _money(monthly_pi)),
        ("Closing pct", _pct(fm.get("closing_pct"))),
        ("Total cash invested", _money(total_cash_invested)),
        ("Property tax rate", _pct(fm.get("property_tax_rate"))),
        ("HOA / mo", _money(fm.get("hoa_monthly"))),
        ("Vacancy pct", _pct(fm.get("vacancy_pct"))),
        ("PM pct", _pct(fm.get("pm_pct"))),
        ("Maintenance pct", _pct(fm.get("maintenance_pct"))),
        ("Capex pct", _pct(fm.get("capex_pct"))),
        ("Insurance rate / yr", _pct(fm.get("insurance_annual_rate"))),
        (
            "Warranty maint offset (yr 1)",
            _pct(fm.get("warranty_maintenance_offset_year_1")),
        ),
        ("Rent / mo (total)", _money(fm.get("rent_total_monthly"))),
        ("Rent / unit", _money(fm.get("rent_per_unit_monthly"))),
        (
            "Rent comp count",
            str(fm["rent_comp_count"])
            if fm.get("rent_comp_count") is not None
            else "override",
        ),
        (
            "Redfin rent estimate",
            _money(fm.get("redfin_rent_estimate"))
            if fm.get("redfin_rent_estimate") is not None
            else "—",
        ),
        ("Rent triangulation", str(fm.get("rent_triangulation_verdict") or "—")),
    ]
    out = ["| Input | Value |", "|---|---|"]
    for k, v in rows:
        out.append(f"| {k} | {v} |")
    return (
        "\n".join(out)
        + "\n\nEdit any number in this file's frontmatter and re-run `re cashflow <address>` — outputs will recompute, your hand-authored sections (Pipeline notes, Backlinks) stay intact.\n"
    )


def _render_property_facts(
    fm: dict[str, Any],
    agg: dict[str, Any],
    flags: list[str],
    diagnostics: dict[str, Any] | None = None,
) -> str:
    """Render the non-financial property dossier: specs, schools, scores,
    and where the tax / HOA / insurance numbers came from.

    Financial provenance reads the FINAL frontmatter values (always set
    post-hydration, so this stays correct on skip-network re-runs).
    Schools / scores / home_type come from the live lookup `agg`, which is
    empty on a skip-network re-run — we say so explicitly in that case.
    """
    agg = agg or {}
    have_lookup = bool(agg)
    out: list[str] = []

    # Key specs line — prefer frontmatter, fill from the live lookup
    specs = []
    if fm.get("year_built"):
        specs.append(f"built {fm['year_built']}")
    if agg.get("home_type"):
        specs.append(str(agg["home_type"]).lower())
    if agg.get("beds") is not None and agg.get("baths") is not None:
        specs.append(f"{agg.get('beds')} bed / {agg.get('baths')} bath")
    if fm.get("sqft"):
        specs.append(f"{fm['sqft']:,} sqft")
    if agg.get("lot_size"):
        specs.append(f"{agg['lot_size']:,} sqft lot")
    if specs:
        out.append("**Specs.** " + ", ".join(specs) + ".")

    def _as_int(v):
        try:
            return int(float(v))
        except (TypeError, ValueError):
            return None

    dom = _as_int(fm.get("days_on_market"))
    rdom = _as_int(fm.get("rental_dom_median"))
    timing = []
    if dom is not None:
        timing.append(f"listed for sale {dom} days")
    if rdom is not None:
        timing.append(f"comparable rentals lease in ~{rdom} days (median)")
    if timing:
        out.append("**Market timing.** " + "; ".join(timing) + ".")

    # Data provenance — based on the values actually used (frontmatter) plus
    # whether a fallback flag fired this run.
    prov = []
    rf_has = bool(fm.get("redfin_url"))
    zw_has = bool(fm.get("zillow_url"))
    if rf_has and zw_has:
        src = "Redfin + Zillow"
    elif zw_has:
        src = "Zillow only (Redfin not resolved)"
    elif rf_has:
        src = "Redfin only (Zillow not resolved)"
    else:
        src = "manual / skip-network inputs"
    prov.append(f"Sources: {src}.")

    tax_fallback = any("property_tax_rate fell back" in f for f in (flags or []))
    if fm.get("property_tax_rate") is not None:
        rate_pct = fm["property_tax_rate"] * 100  # frontmatter stores a fraction
        if tax_fallback:
            prov.append(
                f"Tax rate {rate_pct:.2f}% is a state-bench fallback (no rate in the listing)."
            )
        else:
            prov.append(f"Tax rate {rate_pct:.2f}% from listing data.")
    hoa = fm.get("hoa_monthly")
    if hoa:
        prov.append(f"HOA {_money(hoa)}/mo from listing.")
    else:
        prov.append("No HOA (assumed $0).")
    if fm.get("annual_insurance"):
        prov.append(f"Insurance {_money(fm['annual_insurance'])}/yr from listing.")
    else:
        prov.append(
            f"Insurance estimated at {_pct(fm.get('insurance_annual_rate'))}/yr (no figure in listing)."
        )
    out.append("**Data provenance.** " + " ".join(prov))

    # Surface the degraded-Zillow-record warning if the lookup flagged it.
    degraded = (diagnostics or {}).get("zillow_degraded_record")
    if degraded:
        out.append(f"**Zillow data note.** {degraded}")

    # Walk / transit / bike scores (live-lookup only)
    scores = []
    for label, key in (
        ("Walk", "walk_score"),
        ("Transit", "transit_score"),
        ("Bike", "bike_score"),
    ):
        v = agg.get(key)
        if isinstance(v, (int, float)) and v:
            scores.append(f"{label} {int(v)}")
    if scores:
        out.append("**Scores.** " + ", ".join(scores) + ".")

    # Schools (live-lookup only)
    schools = agg.get("schools") or []
    if schools:
        rows = ["", "| School | Level | Rating | Distance |", "|---|---|---|---|"]
        for s in schools[:8]:
            if not isinstance(s, dict):
                continue
            name = s.get("name") or "—"
            level = s.get("level") or s.get("type") or "—"
            rating = s.get("rating")
            rating_str = f"{rating}/10" if rating not in (None, "", 0) else "—"
            dist = s.get("distance")
            dist_str = f"{dist} mi" if dist not in (None, "") else "—"
            rows.append(f"| {name} | {level} | {rating_str} | {dist_str} |")
        out.append("**Schools.**" + "\n".join(rows))
    elif not have_lookup:
        out.append(
            "**Schools.** Not refreshed this run (skip-network: price + rent were "
            "already in frontmatter). Delete the file or pass no --price/--rent to "
            "pull schools from a live lookup."
        )
    else:
        out.append(
            "**Schools.** None returned (Redfin is the reliable school source; "
            "Zillow lazy-loads schools after page render so they're often absent "
            "when only Zillow resolved)."
        )

    return "\n\n".join(out) + "\n"


def _is_url(s: str) -> bool:
    return s.startswith("http://") or s.startswith("https://")


def _maybe_existing_frontmatter(
    slug: str, properties_dir: str
) -> tuple[dict[str, Any], str]:
    path = os.path.join(properties_dir, f"{slug}.md")
    if not os.path.exists(path):
        return {}, ""
    with open(path) as f:
        return _parse_frontmatter(f.read())


_ZPID_RE = re.compile(r"/(\d+)_zpid/?")
_REDFIN_ID_RE = re.compile(r"/home/(\d+)/?$")


def _extract_zpid(url: str | None) -> str | None:
    if not url or not isinstance(url, str):
        return None
    m = _ZPID_RE.search(url)
    return m.group(1) if m else None


def _extract_redfin_id(url: str | None) -> str | None:
    if not url or not isinstance(url, str):
        return None
    m = _REDFIN_ID_RE.search(url)
    return m.group(1) if m else None


def _find_existing_slug_by_property_id(
    *, zpid: str | None, redfin_id: str | None, properties_dir: str
) -> str | None:
    if not zpid and not redfin_id:
        return None
    if not os.path.isdir(properties_dir):
        return None
    for fname in os.listdir(properties_dir):
        if not fname.endswith(".md"):
            continue
        path = os.path.join(properties_dir, fname)
        try:
            with open(path) as f:
                fm, _ = _parse_frontmatter(f.read())
        except OSError:
            continue
        existing_zpid = _extract_zpid(
            fm.get("zillow_url") if isinstance(fm.get("zillow_url"), str) else None
        )
        existing_redfin = _extract_redfin_id(
            fm.get("redfin_url") if isinstance(fm.get("redfin_url"), str) else None
        )
        if zpid and existing_zpid == zpid:
            return fname[:-3]
        if redfin_id and existing_redfin == redfin_id:
            return fname[:-3]
    return None


def _beds_per_unit(
    fm: dict[str, Any], agg: dict[str, Any], units: int, cli: dict[str, Any]
) -> tuple[int, bool]:
    """Infer bedrooms per unit for the FMR lookup. Returns (beds, assumed)."""
    bpu = cli.get("beds_per_unit") or fm.get("section8_beds_per_unit")
    if bpu:
        return int(bpu), False
    total_beds = agg.get("beds") or fm.get("beds")
    if total_beds and units:
        return max(0, round(total_beds / units)), False
    return 2, True


def _section8_for(
    fm: dict[str, Any],
    agg: dict[str, Any],
    units: int,
    cli: dict[str, Any],
    flags: list[str],
) -> tuple[str | None, dict[str, Any]]:
    """Compute the Section 8 voucher section + the scoring fields to persist.

    Returns (markdown_or_None, frontmatter_updates). Degrades gracefully: a
    missing ZIP/rent skips it; a ZIP outside SAFMR coverage renders a short
    'unavailable' note rather than failing the whole cashflow run."""
    import fmr as _fmr
    import section8 as _s8

    zip_code = fm.get("zip") or agg.get("zip")
    market_total = fm.get("rent_total_monthly")
    if not zip_code:
        flags.append("Section 8 skipped: no ZIP resolved")
        return None, {}
    if not market_total:
        flags.append("Section 8 skipped: no market rent")
        return None, {}

    bpu, assumed = _beds_per_unit(fm, agg, units, cli)
    psp = cli.get("payment_standard_pct")
    if psp is None:
        psp = fm.get("payment_standard_pct", 1.0)
    util = cli.get("utility_allowance")
    if util is None:
        util = fm.get("section8_utility_allowance", 0.0)
    token = cli.get("hud_token") or os.environ.get("HUD_API_TOKEN")

    fmr_res = _fmr.lookup(zip_code, year=cli.get("fmr_year"), token=token)
    if not fmr_res.get("ok"):
        flags.append(
            f"Section 8 FMR unavailable for {zip_code}: {fmr_res.get('error')}"
        )
        return _s8.render_markdown(fmr_res), {}

    res = _s8.analyze(
        units=units,
        beds_per_unit=bpu,
        market_rent_total_monthly=float(market_total),
        fmr_by_beds={int(k): v for k, v in fmr_res["fmr"].items()},
        payment_standard_pct=psp,
        utility_allowance_per_unit=util,
        beds_assumed=assumed,
        fmr_meta={
            k: fmr_res.get(k)
            for k in ("area_name", "fiscal_year", "source", "zip", "is_small_area")
        },
    )
    if not res.get("ok"):
        return _s8.render_markdown(res), {}

    tt = res["totals"]
    updates: dict[str, Any] = {
        "section8_beds_per_unit": bpu,
        "payment_standard_pct": psp,
        "section8_classification": res["classification"],
        "section8_income_stability": res["income_stability"],
        "section8_rent_total": tt["section8_typical"],
        "section8_premium_total": tt["premium_vs_market"],
        "section8_premium_pct": tt["premium_pct"],
        "fmr_area_name": fmr_res.get("area_name"),
        "fmr_fiscal_year": fmr_res.get("fiscal_year"),
    }
    if util:
        updates["section8_utility_allowance"] = util
    return _s8.render_markdown(res), updates


def _neighborhood_for(
    fm: dict[str, Any], agg: dict[str, Any], cli: dict[str, Any], flags: list[str]
) -> tuple[str | None, dict[str, Any]]:
    """Compute the neighborhood section (demographics + crime) + scoring fields."""
    import neighborhood as _nb

    zip_code = fm.get("zip") or agg.get("zip")
    if not zip_code:
        flags.append("Neighborhood skipped: no ZIP resolved")
        return None, {}
    city = fm.get("city") or agg.get("city")
    state = fm.get("state") or agg.get("state")
    key = cli.get("census_key") or os.environ.get("CENSUS_API_KEY")

    res = _nb.lookup(zip_code, city=city, state=state, census_key=key)
    flags.extend(res.get("flags", []))

    updates: dict[str, Any] = {}
    acs = res.get("acs") or {}
    crime = res.get("crime") or {}
    if acs.get("median_hh_income") is not None:
        updates["nbhd_median_income"] = acs["median_hh_income"]
    if acs.get("poverty_rate") is not None:
        updates["nbhd_poverty_rate"] = acs["poverty_rate"]
    if acs.get("pct_renter") is not None:
        updates["nbhd_pct_renter"] = acs["pct_renter"]
    if crime.get("violent_rate_per_100k") is not None:
        updates["nbhd_violent_crime_per_100k"] = crime["violent_rate_per_100k"]
    # School rating is the best free, sub-ZIP proxy for neighborhood stability
    # (adversarial review 2026-06) -- crime here is only city-level, so every
    # Cleveland-proper ZIP looks identical. Average the scraped ratings (1-10).
    ratings = [
        float(s["rating"])
        for s in (agg.get("schools") or [])
        if isinstance(s, dict)
        and str(s.get("rating") or "").replace(".", "", 1).isdigit()
    ]
    if ratings:
        updates["nbhd_school_rating"] = round(sum(ratings) / len(ratings), 1)

    # --- Area-specific vacancy (Change 2) ---
    # Derive nbhd_vacancy_pct from a defensible signal, clamped to 5-15%.
    # Method:
    #   1. FMR tightness proxy: compare HUD FMR (from section8 data already on
    #      fm) vs ACS median gross rent. FMR/MGR > 1 means tight supply (HUD
    #      paying over market) -> lower vacancy; < 1 means soft market -> higher.
    #   2. Renter-share proxy: high renter share (>=50%) suggests rental depth
    #      and a liquid market -> lean toward the tighter end of the band.
    # Both signals are soft; output is always clamped to [5%, 15%].
    _VACANCY_MIN, _VACANCY_MAX = 0.05, 0.15
    vacancy_derived: float | None = None
    vacancy_method: str | None = None

    fmr_by_beds: dict = fm.get("fmr_by_beds") or {}
    beds_per_unit: int | None = fm.get("section8_beds_per_unit")
    mgr = acs.get("median_gross_rent") if isinstance(acs, dict) else None
    if fmr_by_beds and beds_per_unit is not None and mgr and mgr > 0:
        fmr_val = fmr_by_beds.get(str(beds_per_unit)) or fmr_by_beds.get(beds_per_unit)
        if isinstance(fmr_val, (int, float)) and fmr_val > 0:
            # tightness = FMR / median_gross_rent; >1 means FMR is generous vs
            # market (HUD paying a premium = tight supply = lower vacancy).
            # Map tightness linearly: 0.7 -> 15% vacancy, 1.3 -> 5% vacancy.
            tightness = fmr_val / mgr
            v = _VACANCY_MAX - (tightness - 0.7) / 0.6 * (_VACANCY_MAX - _VACANCY_MIN)
            vacancy_derived = round(max(_VACANCY_MIN, min(_VACANCY_MAX, v)), 4)
            vacancy_method = (
                f"FMR tightness ratio {tightness:.2f} (FMR ${fmr_val:,.0f} / "
                f"ACS median rent ${mgr:,.0f}) -> {vacancy_derived * 100:.0f}%"
            )
    elif (
        isinstance(acs, dict)
        and isinstance(acs.get("pct_renter"), (int, float))
        and mgr
    ):
        # Renter-share proxy only: high renter share with decent rent depth
        # suggests a liquid rental market; lean toward tighter vacancy.
        pct_r = acs["pct_renter"]
        if pct_r >= 0.5:
            vacancy_derived = round(max(_VACANCY_MIN, 0.10 - (pct_r - 0.5) * 0.10), 4)
            vacancy_method = (
                f"renter share {pct_r * 100:.0f}% -> {vacancy_derived * 100:.0f}%"
            )

    if vacancy_derived is not None:
        updates["nbhd_vacancy_pct"] = vacancy_derived
        updates["nbhd_vacancy_method"] = vacancy_method

    return _nb.render_markdown(res), updates


def _flood_zone_for(
    address: str, agg: dict[str, Any], flags: list[str]
) -> dict[str, Any]:
    """Lookup FEMA NFHL flood zone for this property via ArcGIS REST.

    Geocoding chain: lat/lng from Redfin/Zillow scrape (already in agg) first,
    Census Geocoder fallback. FEMA NFHL layer 28 (Flood Hazard Areas) returns
    FLD_ZONE, SFHA_TF, and ZONE_SUBTY for the parcel point.

    Returns {} on any failure (never raises) so flood zone is an optional enrichment.
    Zone codes: X = minimal risk, AE/A = 100-year SFHA, VE = coastal, X500 = 500-yr.
    SFHA_TF = 'T' means Special Flood Hazard Area (mandatory insurance required).
    """
    import urllib.request as _ur
    import urllib.parse as _up

    lat = agg.get("lat")
    lng = agg.get("lng")

    # Fallback: Census Geocoder (free, no key, ~1s latency).
    if lat is None or lng is None:
        try:
            geo_url = (
                "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
                f"?address={_up.quote(address)}&benchmark=2020&format=json"
            )
            with _ur.urlopen(geo_url, timeout=12) as _r:
                _geo = __import__("json").load(_r)
            _m = (_geo.get("result") or {}).get("addressMatches") or []
            if _m:
                lng = _m[0]["coordinates"]["x"]
                lat = _m[0]["coordinates"]["y"]
        except Exception as _e:
            flags.append(f"flood-zone: geocoder failed ({str(_e)[:60]})")
            return {}

    if lat is None or lng is None:
        flags.append("flood-zone: no coordinates available")
        return {}

    try:
        fema_url = (
            "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query"
            f"?geometry={lng},{lat}&geometryType=esriGeometryPoint&inSR=4326"
            "&spatialRel=esriSpatialRelWithin&outFields=FLD_ZONE,SFHA_TF,ZONE_SUBTY"
            "&returnGeometry=false&f=json"
        )
        with _ur.urlopen(fema_url, timeout=12) as _r2:
            _fema = __import__("json").load(_r2)
        _feats = _fema.get("features") or []
        if not _feats:
            flags.append("flood-zone: FEMA returned no features (may be unmapped area)")
            return {"lat": lat, "lng": lng}
        _a = _feats[0]["attributes"]
        zone = _a.get("FLD_ZONE") or "?"
        sfha = _a.get("SFHA_TF") == "T"
        subtype = _a.get("ZONE_SUBTY") or None
        return {
            "lat": lat,
            "lng": lng,
            "flood_zone": zone,
            "flood_sfha": sfha,
            "flood_zone_subtype": subtype,
        }
    except Exception as _e:
        flags.append(f"flood-zone: FEMA API failed ({str(_e)[:60]})")
        return {"lat": lat, "lng": lng}


# Property types this strategy never wants: shared-ownership / HOA-bound
# (condo, townhouse, co-op) and 5+ unit commercial. Single-family and 2-4 unit
# multifamily are kept — you own the whole building, no HOA, no shared systems.
_EXCLUDED_HOME_TYPES = {"condo", "townhouse", "co-op", "coop"}


def _multi_unit_count(name: str, rf: dict, agg: dict) -> int | None:
    """Best-effort exact unit count (2-4) for a genuine multifamily, else None.

    Redfin tags every small multifamily with the range "Multi-Family (2-4 Unit)",
    so an exact count usually only appears in parcel records or the remarks."""
    pub = rf.get("public_records") or {}
    for src in (pub.get("basicInfo") or {}, pub.get("latestListingInfo") or {}, agg):
        for k in ("numUnits", "unitCount", "units", "numberOfUnits"):
            v = src.get(k)
            if isinstance(v, (int, float)) and 2 <= v <= 4:
                return int(v)
    text = f"{name} {rf.get('listing_remarks') or ''}".lower()
    if (
        "fourplex" in text
        or "quad" in text
        or "four family" in text
        or "4-family" in text
    ):
        return 4
    if "triplex" in text or "three family" in text or "3-family" in text:
        return 3
    if (
        "duplex" in text
        or "two family" in text
        or "two-family" in text
        or "2-family" in text
    ):
        return 2
    return None


def _classify_property(
    pre_lookup: dict[str, Any] | None,
) -> tuple[str, int | None, float, str | None]:
    """Read the listing's real type + unit count + HOA from the scrape.

    Returns (property_type, units, hoa_monthly, exclude_reason). This is the guard
    against two bugs: (a) including condos/townhouses/co-ops (shared ownership +
    HOA + shared plumbing), and (b) fabricating units by defaulting a single
    dwelling to "2 units" and doubling its rent. Most reliable signal first:
    Redfin public-records propertyTypeName, then the aggregated home_type.
    Unknown/ambiguous resolves to a single unit — never invent rent we can't see."""
    agg = (pre_lookup or {}).get("aggregate") or {}
    rf = (pre_lookup or {}).get("redfin") or {}
    pub = rf.get("public_records") or {}
    name = (
        (pub.get("latestListingInfo") or {}).get("propertyTypeName")
        or (pub.get("basicInfo") or {}).get("propertyTypeName")
        or ""
    )
    home_type = (agg.get("home_type") or rf.get("property_type") or "").lower()
    hoa = agg.get("monthly_hoa_fee")
    if hoa is None:
        hoa = (pub.get("mortgageCalculatorInfo") or {}).get("monthlyHoaDues")
    hoa = float(hoa) if isinstance(hoa, (int, float)) else 0.0

    n = name.lower()
    if "condo" in n or "co-op" in n or "coop" in n:
        return (
            "condo/co-op",
            None,
            hoa,
            f"{name or home_type} (shared ownership / HOA)",
        )
    if "townhouse" in n or home_type == "townhouse":
        if hoa and hoa > 0:
            return (
                "townhouse",
                None,
                hoa,
                f"Townhouse with HOA ${hoa:.0f}/mo (shared ownership / HOA)",
            )
        # Fee-simple rowhome / townhouse with $0 HOA — standard residential ownership
        return ("townhouse", _multi_unit_count(name, rf, agg) or 1, 0.0, None)
    if home_type in {"condo", "co-op", "coop"}:
        return (home_type, None, hoa, f"{home_type} (shared ownership / HOA)")
    if "5+" in n or "5 +" in n or "five or more" in n or "(5+" in n:
        return ("multi-family-5+", None, hoa, "5+ unit (commercial, out of strategy)")
    if hoa and hoa > 0:
        return (home_type or "unknown", None, hoa, f"has HOA ${hoa:.0f}/mo")

    if "multi" in n or home_type == "multi-family":
        return ("multi-family", _multi_unit_count(name, rf, agg) or 2, hoa, None)
    if "single" in n or home_type == "single-family":
        return ("single-family", 1, hoa, None)
    # Ambiguous / "other" / missing: model as one dwelling, never double the rent.
    return (home_type or "unknown", 1, hoa, None)


def run(
    address: str,
    *,
    save: bool = True,
    output_dir: str | None = None,
    **cli_overrides: Any,
) -> dict:
    flags: list[str] = []
    cli = {k: v for k, v in cli_overrides.items() if v is not None}
    properties_dir = output_dir or _default_properties_dir()

    is_url_input = _is_url(address)
    redfin_url = cli.get("redfin_url")
    zillow_url = cli.get("zillow_url")
    if is_url_input:
        if "zillow.com" in address:
            zillow_url = zillow_url or address
        elif "redfin.com" in address:
            redfin_url = redfin_url or address

    tentative_slug = slugify_address(address) if not is_url_input else None
    pre_fm: dict[str, Any] = {}
    pre_body = ""
    if tentative_slug:
        pre_fm, pre_body = _maybe_existing_frontmatter(tentative_slug, properties_dir)
        zillow_url = zillow_url or (
            pre_fm.get("zillow_url")
            if isinstance(pre_fm.get("zillow_url"), str)
            else None
        )
        redfin_url = redfin_url or (
            pre_fm.get("redfin_url")
            if isinstance(pre_fm.get("redfin_url"), str)
            else None
        )

    have_price = cli.get("price") is not None or pre_fm.get("price") is not None
    have_rent = (
        cli.get("rent_total_monthly") is not None
        or cli.get("rent_per_unit_monthly") is not None
        or pre_fm.get("rent_total_monthly") is not None
    )
    pre_lookup: dict[str, Any] | None = None
    canonical_address = address
    if not (have_price and have_rent) or is_url_input:
        pre_lookup = lookup.lookup(
            address, redfin_url=redfin_url, zillow_url=zillow_url
        )
        agg = pre_lookup.get("aggregate") or {}
        if agg.get("address"):
            parts = [
                agg.get("address"),
                agg.get("city"),
                agg.get("state"),
                agg.get("zip"),
            ]
            canonical_address = " ".join(p for p in parts if p)
        elif is_url_input:
            return {
                "error": "URL did not resolve to a property; pass an address instead",
                "input": address,
                "flags": flags,
            }

    # Guard: read the real property type + unit count, drop condos/townhouses/
    # co-ops/5+unit/HOA before underwriting (and feed the true unit count below
    # so a single dwelling never gets its rent doubled). --allow-any-type bypasses.
    classified_type, classified_units, classified_hoa, exclude_reason = (
        _classify_property(pre_lookup)
    )
    if exclude_reason and not cli.get("allow_any_type"):
        return {
            "excluded": True,
            "reason": exclude_reason,
            "property_type": classified_type,
            "hoa_monthly": classified_hoa,
            "address": canonical_address,
            "flags": flags,
        }

    target_zpid = _extract_zpid(
        pre_lookup.get("zillow_url") if pre_lookup else zillow_url
    )
    target_redfin_id = _extract_redfin_id(
        pre_lookup.get("redfin_url") if pre_lookup else redfin_url
    )
    dedup_slug = _find_existing_slug_by_property_id(
        zpid=target_zpid,
        redfin_id=target_redfin_id,
        properties_dir=properties_dir,
    )
    if dedup_slug:
        slug = dedup_slug
    else:
        slug = slugify_address(canonical_address)
    path = os.path.join(properties_dir, f"{slug}.md")

    if slug == tentative_slug:
        existing_fm, existing_body = pre_fm, pre_body
    else:
        existing_fm, existing_body = _maybe_existing_frontmatter(slug, properties_dir)
        if pre_fm and not existing_fm:
            existing_fm = pre_fm
            existing_body = pre_body

    if not existing_fm.get("zip") and canonical_address:
        m_sz = re.search(r'\b([A-Za-z]{2})\s+(\d{5})\b', canonical_address)
        if m_sz:
            if not existing_fm.get("state"):
                existing_fm["state"] = m_sz.group(1).upper()
            existing_fm["zip"] = m_sz.group(2)

    # Explicit --units wins; otherwise the scraped count (1 for a single dwelling,
    # 2-4 for real multifamily) beats any stale value in an existing dossier.
    units = (
        cli.get("units")
        or classified_units
        or existing_fm.get("units")
        or DEFAULTS["units"]
    )

    facts, fl = _hydrate_property_facts(existing_fm, cli, pre_lookup)
    flags.extend(fl)

    radius_miles = cli.get("radius_miles")
    if radius_miles is None:
        radius_miles = existing_fm.get("radius_miles")
    if radius_miles is None:
        radius_miles = 1.0
    max_radius_miles = cli.get("max_radius_miles")
    if max_radius_miles is None:
        max_radius_miles = existing_fm.get("max_radius_miles")
    if max_radius_miles is None:
        max_radius_miles = 3.0
    target_comp_count = cli.get("target_comp_count")
    if target_comp_count is None:
        target_comp_count = existing_fm.get("target_comp_count")
    if target_comp_count is None:
        target_comp_count = 40
    beds_tolerance = cli.get("beds_tolerance")
    if beds_tolerance is None:
        beds_tolerance = existing_fm.get("beds_tolerance")
    if beds_tolerance is None:
        beds_tolerance = 0

    rent, fl, _est = _hydrate_rent(
        canonical_address,
        existing_fm,
        cli,
        units,
        radius_miles=radius_miles,
        max_radius_miles=max_radius_miles,
        target_comp_count=target_comp_count,
        beds_tolerance=beds_tolerance,
        zillow_url=facts.get("zillow_url") or zillow_url,
        redfin_url=facts.get("redfin_url") or redfin_url,
        pre_lookup=pre_lookup,
    )
    flags.extend(fl)

    if facts.get("price") is None:
        return {"error": "no price found; pass --price <amount>", "flags": flags}
    if rent.get("rent_total_monthly") is None:
        return {
            "error": flags[-1] if flags else "no rent",
            "flags": flags,
            "facts": facts,
            "rent": rent,
        }

    fm: dict[str, Any] = {
        "slug": slug,
        "type": "property",
        "address": canonical_address,
        "city": existing_fm.get("city"),
        "state": existing_fm.get("state") or (re.search(r'\b([A-Za-z]{2})\s+(\d{5})\b', canonical_address).group(1).upper() if re.search(r'\b([A-Za-z]{2})\s+(\d{5})\b', canonical_address) else None),
        "zip": existing_fm.get("zip") or (re.search(r'\b([A-Za-z]{2})\s+(\d{5})\b', canonical_address).group(2) if re.search(r'\b([A-Za-z]{2})\s+(\d{5})\b', canonical_address) else None),
        "status": existing_fm.get("status") or "prospect",
        "purpose": existing_fm.get("purpose") or "investment",
        "acquired_at": existing_fm.get("acquired_at"),
        "last_touched": _dt.date.today().isoformat(),
        "units": units,
        "property_type": classified_type,
        **facts,
        **rent,
        "radius_miles": radius_miles,
        "max_radius_miles": max_radius_miles,
        "target_comp_count": target_comp_count,
        "beds_tolerance": beds_tolerance,
    }
    for k, default in DEFAULTS.items():
        if k == "units":
            continue
        if cli.get(k) is not None:
            fm[k] = cli[k]
        elif existing_fm.get(k) is not None:
            fm[k] = existing_fm[k]
        else:
            fm[k] = default

    price = float(fm["price"])
    down_payment = price * fm["down_pct"]
    closing_costs = price * fm["closing_pct"]
    # Upfront make-ready / deferred-maintenance buy-down on cheap class-C stock is
    # real cash out the door -- count it in the basis so cash-on-cash is honest.
    rehab = float(fm.get("rehab_per_unit") or 0) * units
    total_cash_invested = down_payment + closing_costs + rehab
    loan = price - down_payment
    monthly_pi = _monthly_pi(loan, fm["interest_rate"], int(fm["term_years"]))

    # On a sale the county reassesses toward the purchase price, so the listing's
    # historical tax understates the go-forward bill. When the market sets an
    # effective_tax_rate, apply it to the purchase PRICE (reassessment reality);
    # else fall back to the listing/state-bench rate.
    eff_rate = fm.get("effective_tax_rate")
    if eff_rate:
        prop_tax_monthly = (price * float(eff_rate)) / 12.0
    else:
        prop_tax_monthly = (price * fm["property_tax_rate"]) / 12.0
    # --- Early Flood Zone Resolution ---
    # Query FEMA NFHL before insurance & parcel calculations so mandatory
    # flood insurance ($175/mo) is properly captured in PITIA, OpEx, and parcel scoring.
    if fm.get("flood_zone") is None:
        _flood_res = _flood_zone_for(
            canonical_address, (pre_lookup or {}).get("aggregate") or {}, flags
        )
        if _flood_res.get("flood_zone"):
            fm["flood_zone"] = _flood_res.get("flood_zone")
            fm["flood_sfha"] = _flood_res.get("flood_sfha")
            fm["flood_zone_subtype"] = _flood_res.get("flood_zone_subtype")

    if fm.get("annual_insurance"):
        insurance_monthly = float(fm["annual_insurance"]) / 12.0
    else:
        insurance_monthly = (price * fm["insurance_annual_rate"]) / 12.0

    # If property is in FEMA Special Flood Hazard Area (SFHA), add mandatory flood insurance
    if fm.get("flood_sfha"):
        flood_ins_monthly = 175.0  # ~$2,100/yr typical NFIP residential coverage
        insurance_monthly += flood_ins_monthly
        flags.append(
            f"flood-zone: SFHA Zone {fm.get('flood_zone')} detected; added ${flood_ins_monthly:.0f}/mo (${flood_ins_monthly*12:.0f}/yr) mandatory flood insurance"
        )

    base = dict(
        gross_rent_monthly=float(fm["rent_total_monthly"]),
        monthly_pi=monthly_pi,
        prop_tax_monthly=prop_tax_monthly,
        insurance_monthly=insurance_monthly,
        hoa_monthly=float(fm.get("hoa_monthly") or 0),
        vacancy_pct=fm["vacancy_pct"],
        pm_pct=fm["pm_pct"],
        capex_pct=fm["capex_pct"],
        utilities_pct=fm.get("utilities_pct") or 0.0,
        opex_floor_pct=fm.get("opex_floor_pct") or 0.0,
    )
    stab = _scenario(maintenance_pct=fm["maintenance_pct"], **base)
    yr1 = _scenario(
        maintenance_pct=fm["maintenance_pct"]
        * (1 - fm["warranty_maintenance_offset_year_1"]),
        **base,
    )

    def _returns(scn: dict) -> dict:
        return {
            "cap_rate": round(scn["noi_annual"] / price, 4) if price else None,
            "cash_on_cash": round(scn["cash_flow_annual"] / total_cash_invested, 4)
            if total_cash_invested
            else None,
        }

    stab.update(_returns(stab))
    yr1.update(_returns(yr1))
    fm["cash_on_cash"] = stab.get("cash_on_cash")
    fm["total_cash_invested"] = total_cash_invested
    fm["cash_to_close"] = total_cash_invested
    fm["total_cash_to_close"] = total_cash_invested

    # Adversarial worst-case + risk metrics, surfaced alongside the realistic case.
    downside = _downside(stab, base, fm, units)
    downside["worst_case"].update(_returns(downside["worst_case"]))
    fm["worst_case_cash_flow_monthly"] = downside["worst_case"]["cash_flow_monthly"]
    fm["worst_case_cap_rate"] = downside["worst_case"]["cap_rate"]
    fm["break_even_occupancy"] = downside["break_even_occupancy"]
    fm["one_unit_vacant_cash_flow_monthly"] = downside[
        "one_unit_vacant_cash_flow_monthly"
    ]
    fm["reserve_recommended"] = downside["reserve_recommended"]

    sections = _split_sections(existing_body)
    intro_text = ""
    non_owned: list[tuple[str, str]] = []
    seen_headings: set[str] = set()
    for heading, content in sections:
        if heading is None:
            intro_text = content
            continue
        if heading in _OWNED_SECTIONS:
            continue
        non_owned.append((heading, content))
        seen_headings.add(heading)

    if not intro_text.strip().startswith("#"):
        intro_text = f"# {canonical_address}\n\n"

    if "Pipeline notes" not in seen_headings:
        today = _dt.date.today().isoformat()
        non_owned.insert(
            0,
            (
                "Pipeline notes",
                f"- {today} first looked.\n- Open questions:\n- Next action:\n",
            ),
        )
    if "Backlinks" not in seen_headings:
        non_owned.append(("Backlinks", "\n"))

    owned: dict[str, str] = {
        "Cash flow": _render_cashflow(stab, yr1) + "\n",
        "Downside & risk": _render_downside(downside, stab) + "\n",
        "Pro forma detail": "Stabilized, monthly:\n\n" + _render_pro_forma(stab) + "\n",
        "Property & neighborhood": _render_property_facts(
            fm,
            (pre_lookup or {}).get("aggregate") or {},
            flags,
            (pre_lookup or {}).get("diagnostics") or {},
        )
        + "\n",
        "Assumptions": _render_assumptions(fm) + "\n",
        "Inputs used": _render_inputs_used(fm, total_cash_invested, loan, monthly_pi)
        + "\n",
    }

    if not cli.get("no_section8"):
        s8_md, s8_upd = _section8_for(
            fm, (pre_lookup or {}).get("aggregate") or {}, units, cli, flags
        )
        if s8_upd:
            fm.update(s8_upd)
            s8_total = s8_upd.get("section8_rent_total")
            if s8_total:
                s8_scn = _scenario(
                    maintenance_pct=fm["maintenance_pct"],
                    **{**base, "gross_rent_monthly": float(s8_total)},
                )
                s8_cf = round(s8_scn["cash_flow_annual"] / 12)
                mkt_cf = round(stab["cash_flow_annual"] / 12)
                fm["section8_cash_flow_monthly"] = s8_cf
                if s8_md:
                    s8_md += (
                        f"\n**Cash flow under Section 8.** Monthly cash flow goes from "
                        f"${mkt_cf:,}/mo at market rent to ${s8_cf:,}/mo on the Section 8 "
                        f"(typical) rent -- a ${s8_cf - mkt_cf:,}/mo swing, government-backed.\n"
                    )
        if s8_md:
            owned["Section 8 voucher"] = s8_md + "\n"
    if not cli.get("no_neighborhood"):
        nb_md, nb_upd = _neighborhood_for(
            fm, (pre_lookup or {}).get("aggregate") or {}, cli, flags
        )
        if nb_upd:
            fm.update(nb_upd)
            # --- Area-specific vacancy (Change 2, wire-in) ---
            # Prefer the neighborhood-derived vacancy over the flat DEFAULTS value
            # when the neighborhood lookup produced a signal-backed estimate.
            nbhd_vac = nb_upd.get("nbhd_vacancy_pct")
            if nbhd_vac is not None and cli.get("vacancy_pct") is None:
                fm["vacancy_pct"] = nbhd_vac
                flags.append(
                    f"vacancy_pct set to {nbhd_vac * 100:.0f}% from neighborhood signal "
                    f"({nb_upd.get('nbhd_vacancy_method', 'area estimate')})"
                )
                # Recompute scenarios with the updated vacancy.
                base["vacancy_pct"] = nbhd_vac
                stab = _scenario(maintenance_pct=fm["maintenance_pct"], **base)
                yr1 = _scenario(
                    maintenance_pct=fm["maintenance_pct"]
                    * (1 - fm["warranty_maintenance_offset_year_1"]),
                    **base,
                )
                stab.update(_returns(stab))
                yr1.update(_returns(yr1))
                downside = _downside(stab, base, fm, units)
                downside["worst_case"].update(_returns(downside["worst_case"]))
                fm["worst_case_cash_flow_monthly"] = downside["worst_case"][
                    "cash_flow_monthly"
                ]
                fm["worst_case_cap_rate"] = downside["worst_case"]["cap_rate"]
                fm["break_even_occupancy"] = downside["break_even_occupancy"]
                fm["one_unit_vacant_cash_flow_monthly"] = downside[
                    "one_unit_vacant_cash_flow_monthly"
                ]
                fm["reserve_recommended"] = downside["reserve_recommended"]
                owned["Cash flow"] = _render_cashflow(stab, yr1) + "\n"
                owned["Downside & risk"] = _render_downside(downside, stab) + "\n"
                owned["Pro forma detail"] = (
                    "Stabilized, monthly:\n\n" + _render_pro_forma(stab) + "\n"
                )
        if nb_md:
            owned["Neighborhood research"] = nb_md + "\n"

    # --- DSCR Loan Underwriting Integration ---
    if not cli.get("no_dscr"):
        try:
            import dscr as _dscr
            price_val = float(fm.get("price") or 0.0)
            gross_rent = float(stab.get("gross_rent_monthly") or 0.0)
            taxes_annual = float(stab.get("prop_tax_monthly", 0.0)) * 12.0
            insurance_annual = float(stab.get("insurance_monthly", 0.0)) * 12.0
            hoa_mo = float(stab.get("hoa_monthly", 0.0))

            if price_val > 0 and gross_rent > 0:
                dscr_res = _dscr.underwrite_dscr(
                    price=price_val,
                    gross_rent_monthly=gross_rent,
                    annual_taxes=taxes_annual,
                    annual_insurance=insurance_annual,
                    monthly_hoa=hoa_mo,
                    target_ltv=float(cli.get("dscr_ltv") or 0.80),
                    annual_rate=float(cli["dscr_rate"]) if cli.get("dscr_rate") is not None else None,
                    product=str(cli.get("dscr_product") or "30yr-fixed"),
                    units=units,
                )
                fm["dscr_ratio"] = dscr_res["dscr"]
                fm["dscr_loan_amount"] = dscr_res["loan_amount"]
                fm["dscr_pitia_monthly"] = dscr_res["pitia_monthly"]
                fm["dscr_interest_rate"] = dscr_res["interest_rate"]
                fm["dscr_tier"] = dscr_res["tier"]
                fm["dscr_clears_min_loan"] = dscr_res["clears_min_loan_floor"]
                fm["dscr_cash_to_close"] = dscr_res["closing_costs"]["total_cash_to_close"]
                fm["dscr_reserves_required"] = dscr_res["reserves"]["liquid_reserves_required"]

                # DSCR financed cash flow (NOI - DSCR Monthly P&I)
                noi_val = float(stab.get("noi_monthly") or 0.0)
                dscr_pi = float(dscr_res["breakdown"]["principal_interest_monthly"])
                dscr_cf = round(noi_val - dscr_pi, 2)
                fm["dscr_cash_flow_monthly"] = dscr_cf

                c2c = round(float(dscr_res["closing_costs"]["total_cash_to_close"]) + rehab, 2)
                fm["total_cash_to_close"] = c2c
                fm["cash_to_close"] = c2c
                dscr_coc = round((dscr_cf * 12.0) / c2c, 4) if c2c > 0 else 0.0
                fm["dscr_cash_on_cash"] = dscr_coc
                fm["cash_on_cash"] = dscr_coc

                # Section 8 Cash Flow under DSCR financing
                s8_total = fm.get("section8_rent_total")
                if s8_total and float(s8_total) > 0:
                    s8_scn = _scenario(
                        maintenance_pct=fm["maintenance_pct"],
                        **{**base, "gross_rent_monthly": float(s8_total)},
                    )
                    s8_noi = float(s8_scn.get("noi_monthly") or 0.0)
                    s8_dscr_cf = round(s8_noi - dscr_pi, 2)
                    s8_dscr_coc = round((s8_dscr_cf * 12.0) / c2c, 4) if c2c > 0 else 0.0
                    fm["section8_dscr_cash_flow_monthly"] = s8_dscr_cf
                    fm["section8_dscr_cash_on_cash"] = s8_dscr_coc
                    fm["section8_cash_flow_monthly"] = round(s8_dscr_cf)

                owned["DSCR financing"] = _dscr.render_markdown(dscr_res) + "\n"
        except Exception as e:
            flags.append(f"DSCR underwriting failed: {e}")

    # --- Parcel Intelligence Integration ---
    if not cli.get("no_parcel"):
        try:
            import parcel as _parcel
            agg = (pre_lookup or {}).get("aggregate") or {}
            parcel_res = _parcel.analyze_parcel(
                address=canonical_address,
                price=fm.get("price"),
                lot_sqft=agg.get("lot_size") or agg.get("lot_sqft"),
                year_built=fm.get("year_built"),
                property_type=fm.get("property_type"),
                units=units,
                beds=agg.get("beds"),
                baths=agg.get("baths"),
                sqft=fm.get("sqft"),
                tax_assessed_value=agg.get("tax_assessed_value"),
                historical_annual_tax=agg.get("annual_property_tax"),
                property_tax_rate=fm.get("property_tax_rate"),
                effective_tax_rate=fm.get("effective_tax_rate") or 0.023,
                apn=agg.get("apn"),
                zoning=agg.get("zoning"),
                flood_zone=fm.get("flood_zone"),
                description_text=agg.get("ai_summary", ""),
            )
            fm["parcel_lot_position"] = parcel_res["site"]["lot_position"]
            fm["parcel_backs_to"] = parcel_res["site"]["backs_to"]
            fm["parcel_zoning"] = parcel_res["zoning"]["classification"]
            fm["parcel_legal_conforming"] = parcel_res["zoning"]["legal_conforming"]
            fm["parcel_score_adj"] = parcel_res.get("score_adjustment", 0)
            fm["projected_reassessed_tax_monthly"] = parcel_res["cadastral"]["projected_reassessed_tax_monthly"]
            fm["tax_shock_monthly"] = parcel_res["cadastral"]["tax_shock_monthly"]
            fm["lead_paint_risk"] = parcel_res["mechanics"]["lead_paint_risk"]
            fm["separate_electric"] = parcel_res["mechanics"]["separate_electric"]
            fm["separate_gas"] = parcel_res["mechanics"]["separate_gas"]

            owned["Parcel intelligence"] = _parcel.render_markdown(parcel_res) + "\n"
        except Exception as e:
            flags.append(f"Parcel analysis failed: {e}")

    # --- Machine-readable provenance (Change 3) ---
    # Build a structured _provenance dict for the five key underwriting inputs.
    # Kept OUT of the YAML frontmatter (would pollute dossier); surfaced in the
    # run() return dict so index_record and callers can consume it.
    listing_url = fm.get("redfin_url") or fm.get("zillow_url")
    tax_source = fm.get("_property_tax_source", "unknown")
    _provenance: dict[str, Any] = {
        "market_rent": {
            "value": fm.get("rent_total_monthly"),
            "source": "Zillow comps"
            if fm.get("rent_comp_count")
            else "Redfin RentalEstimate"
            if fm.get("redfin_rent_estimate")
            else "assumption",
            "source_url": fm.get("zillow_url") or fm.get("redfin_url"),
            "method": (
                f"bbox bed/bath-matched median across {fm.get('rent_comp_count', 0)} comps, "
                f"{int((fm.get('rent_haircut_pct') or 0) * 100)}% haircut"
                if fm.get("rent_comp_count")
                else "Redfin native RentalEstimate"
            ),
        },
        "property_tax": {
            "value": fm.get("annual_property_tax"),
            "source": "Redfin public records"
            if tax_source == "listing"
            else "state bench (Tax Foundation effective rate)",
            "source_url": listing_url if tax_source == "listing" else None,
            "method": "annual tax / price"
            if tax_source == "listing"
            else f"{(fm.get('property_tax_rate') or 0) * 100:.2f}% state bench",
        },
        "insurance": {
            "value": fm.get("annual_insurance")
            or round(price * (fm.get("insurance_annual_rate") or 0.007), 2),
            "source": "Redfin cost-of-ownership"
            if fm.get("annual_insurance")
            else "assumption",
            "source_url": listing_url if fm.get("annual_insurance") else None,
            "method": "parsed annual homeowners insurance"
            if fm.get("annual_insurance")
            else f"{(fm.get('insurance_annual_rate') or 0.007) * 100:.1f}% of price (landlord-policy bench)",
        },
        "hoa": {
            "value": fm.get("hoa_monthly") or 0,
            "source": "Redfin/Zillow listing"
            if (fm.get("hoa_monthly") or 0) > 0
            else "assumption",
            "source_url": listing_url if (fm.get("hoa_monthly") or 0) > 0 else None,
            "method": "parsed HOA from listing"
            if (fm.get("hoa_monthly") or 0) > 0
            else "$0 (no HOA on this property type)",
        },
        "vacancy": {
            "value": fm.get("vacancy_pct"),
            "source": "Census ACS / HUD FMR tightness"
            if fm.get("nbhd_vacancy_pct") is not None
            else "assumption",
            "source_url": None,
            "method": fm.get("nbhd_vacancy_method")
            or "10% industry standard for class-C rentals",
        },
        "maintenance": {
            "value": fm.get("maintenance_pct"),
            "source": "assumption",
            "source_url": None,
            "method": "8% of gross rent (old Rust-Belt stock, frequent repairs)",
        },
        "capex": {
            "value": fm.get("capex_pct"),
            "source": "assumption",
            "source_url": None,
            "method": "8% of rent (roof/furnace/sewer reserve on aged systems)",
        },
        "pm": {
            "value": fm.get("pm_pct"),
            "source": "assumption",
            "source_url": None,
            "method": "10% of gross rent (out-of-state full-service PM)",
        },
        "utilities": {
            "value": fm.get("utilities_pct"),
            "source": "assumption",
            "source_url": None,
            "method": "5% of gross rent (landlord-paid water/sewer/trash on old stock)",
        },
    }
    # Strip the internal flag key from fm before writing to disk.
    fm.pop("_property_tax_source", None)
    fm.pop("nbhd_vacancy_method", None)

    body = _stitch_sections(intro_text, owned, non_owned)
    document = _emit_frontmatter(fm) + "\n" + body

    saved_path: str | None = None
    if save:
        os.makedirs(properties_dir, exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            f.write(document)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
        saved_path = path

    # --- Enrichment fields for index.jsonl ---
    # rent_comps: up to 12 closest-first rent comps from the live estimate_rent run.
    _raw_rent_comps = _est.get("comps") or []
    _rent_comps: list[dict] = []
    for _c in _raw_rent_comps[:12]:
        _rent_comps.append(
            {
                "address": _c.get("address"),
                "beds": _c.get("beds"),
                "baths": _c.get("baths"),
                "sqft": _c.get("sqft"),
                "rent": _c.get("price"),
                "distance_mi": _c.get("distance_miles"),
                "url": _c.get("url"),
                "dom": int(_c["days_on_zillow"])
                if isinstance(_c.get("days_on_zillow"), (int, float))
                else None,
            }
        )

    # rent_comp_basis: metadata about the comp search.
    _target = _est.get("target") or {}
    _rent_comp_basis: dict = {
        "matched_beds": _target.get("beds"),
        "beds_tolerance": _est.get("beds_tolerance"),
        "radius_mi": _est.get("radius_miles_used"),
        "basis": _est.get("estimate_basis"),
    }

    # sale_comps: up to 12 Redfin similar-home sale comps from the lookup.
    _agg_comps = (pre_lookup or {}).get("aggregate", {}).get("comps") or []
    _sale_comps: list[dict] = []
    for _sc in _agg_comps[:12]:
        _sale_comps.append(
            {
                "address": _sc.get("address"),
                "beds": _sc.get("beds"),
                "baths": _sc.get("baths"),
                "sqft": _sc.get("sqft"),
                "price": _sc.get("price"),
                "status": _sc.get("mls_status"),
                "url": _sc.get("url"),
            }
        )

    # description: listing text sourced from the pre_lookup aggregate (which
    # lookup.py populates from redfin "description" then zillow "description"),
    # then directly from each source as fallback; capped at 1500 chars.
    _rf_raw = (pre_lookup or {}).get("redfin") or {}
    _zw_raw = (pre_lookup or {}).get("zillow") or {}
    _desc_raw = (
        (pre_lookup or {}).get("aggregate", {}).get("description")
        or _rf_raw.get("description")
        or _zw_raw.get("description")
    )
    _description: str | None = str(_desc_raw)[:1500] if _desc_raw else None

    # rent_bolsters: canonical feature tags extracted from the description.
    _rent_bolsters: list[str] = extract_rent_bolsters(_description or "")

    return {
        "address": canonical_address,
        "slug": slug,
        "path": saved_path,
        "stabilized": stab,
        "year_1_with_warranty": yr1,
        "downside": downside,
        "frontmatter": fm,
        "flags": flags,
        "_provenance": _provenance,
        "rent_comps": _rent_comps,
        "rent_comp_basis": _rent_comp_basis,
        "sale_comps": _sale_comps,
        "description": _description,
        "rent_bolsters": _rent_bolsters,
        "lat": (pre_lookup or {}).get("aggregate", {}).get("lat"),
        "lng": (pre_lookup or {}).get("aggregate", {}).get("lng"),
        "flood_zone": fm.get("flood_zone"),
        "flood_sfha": fm.get("flood_sfha"),
        "flood_zone_subtype": fm.get("flood_zone_subtype"),
    }


def main(argv=None):
    import argparse
    import json
    import sys

    ap = argparse.ArgumentParser(prog="cashflow")
    ap.add_argument("address", help="address or Redfin/Zillow URL")
    ap.add_argument("--price", type=float)
    ap.add_argument("--sqft", type=int)
    ap.add_argument("--units", type=int)
    ap.add_argument(
        "--allow-any-type",
        action="store_true",
        help="underwrite even condos/townhouses/co-ops/HOA (off by default)",
    )
    ap.add_argument("--rent-per-unit", dest="rent_per_unit_monthly", type=float)
    ap.add_argument("--rent-total", dest="rent_total_monthly", type=float)
    ap.add_argument("--zillow-url")
    ap.add_argument("--redfin-url")
    ap.add_argument("--down-pct", type=float)
    ap.add_argument("--rate", dest="interest_rate", type=float)
    ap.add_argument("--term", dest="term_years", type=int)
    ap.add_argument("--closing-pct", type=float)
    ap.add_argument("--vacancy-pct", type=float)
    ap.add_argument("--pm-pct", type=float)
    ap.add_argument("--maintenance-pct", type=float)
    ap.add_argument("--capex-pct", type=float)
    ap.add_argument(
        "--utilities-pct", type=float, help="landlord water/sewer/trash, %% of gross"
    )
    ap.add_argument(
        "--opex-floor-pct", type=float, help="50%%-rule floor on operating expenses"
    )
    ap.add_argument(
        "--rent-haircut-pct", type=float, help="discount on the optimistic comp rent"
    )
    ap.add_argument(
        "--effective-tax-rate",
        type=float,
        help="tax = price x rate (reassessment-on-sale)",
    )
    ap.add_argument(
        "--rehab-per-unit", type=float, help="upfront make-ready added to cash invested"
    )
    ap.add_argument("--insurance-rate", dest="insurance_annual_rate", type=float)
    ap.add_argument(
        "--annual-insurance", type=float, help="absolute $; overrides insurance-rate"
    )
    ap.add_argument("--property-tax-rate", type=float)
    ap.add_argument("--hoa-monthly", type=float)
    ap.add_argument(
        "--warranty-offset", dest="warranty_maintenance_offset_year_1", type=float
    )
    ap.add_argument("--radius-miles", type=float)
    ap.add_argument("--max-radius-miles", type=float)
    ap.add_argument("--target-comps", dest="target_comp_count", type=int)
    ap.add_argument("--beds-tolerance", type=int)
    ap.add_argument(
        "--output-dir",
        help="dir for the property .md (overrides REAL_ESTATE_PROPERTIES_DIR env var; default ~/CORTANA/workspaces/real-estate/wiki/entities/properties/)",
    )
    ap.add_argument(
        "--no-save",
        action="store_true",
        help="don't write the .md (just print the analysis)",
    )
    ap.add_argument(
        "--no-section8",
        action="store_true",
        help="skip the Section 8 voucher analysis section",
    )
    ap.add_argument(
        "--no-neighborhood",
        action="store_true",
        help="skip the demographics + crime research section",
    )
    ap.add_argument(
        "--no-dscr",
        action="store_true",
        help="skip the DSCR loan financing analysis",
    )
    ap.add_argument(
        "--no-parcel",
        action="store_true",
        help="skip the parcel-by-parcel intelligence analysis",
    )
    ap.add_argument("--dscr-ltv", type=float, help="target DSCR LTV (default 0.75)")
    ap.add_argument("--dscr-rate", type=float, help="explicit DSCR interest rate")
    ap.add_argument(
        "--dscr-product",
        choices=["30yr-fixed", "5/1-arm", "interest-only"],
        default="30yr-fixed",
        help="DSCR loan product (default: 30yr-fixed)",
    )
    ap.add_argument(
        "--beds-per-unit",
        type=int,
        help="bedrooms per unit (else inferred from total beds / units)",
    )
    ap.add_argument(
        "--payment-standard-pct",
        type=float,
        help="Section 8 payment standard as a fraction of FMR (default 1.0)",
    )
    ap.add_argument(
        "--utility-allowance",
        type=float,
        help="tenant-paid utility allowance $/unit for Section 8",
    )
    ap.add_argument(
        "--hud-token",
        help="HUD API token for FMR (else $HUD_API_TOKEN, else no-token bulk file)",
    )
    ap.add_argument(
        "--fmr-year", type=int, help="FMR fiscal year (default: current federal FY)"
    )
    ap.add_argument(
        "--census-key",
        help="Census API key for ACS demographics (else $CENSUS_API_KEY)",
    )
    args = ap.parse_args(argv)

    cli_overrides = {
        k: v
        for k, v in vars(args).items()
        if k not in {"address", "no_save", "output_dir"} and v is not None
    }
    result = run(
        args.address, save=not args.no_save, output_dir=args.output_dir, **cli_overrides
    )
    json.dump(result, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
