#!/usr/bin/env python3
"""Section 8 / Housing Choice Voucher economics for a (small multifamily) rental.

Models what a landlord would actually collect under the Housing Choice Voucher
program (Section 8) and compares it head-to-head with open-market rent, so an
investor can see whether the voucher pays a PREMIUM over market (the classic
edge in soft, low-income ZIPs where HUD's Fair Market Rent outruns street rent)
or a DISCOUNT (higher-rent areas where the rent-reasonableness test caps the
voucher below market).

The voucher economics, briefly:
  - HUD publishes a Fair Market Rent (FMR) per bedroom-size for each area. In
    most metros this is a Small Area FMR set by ZIP (see fmr.py).
  - The local Public Housing Authority (PHA) sets a *payment standard* at
    90-110% of FMR (up to 120% with HUD approval). There is no free per-PHA
    feed, so we model the payment standard as FMR x payment_standard_pct.
  - The PHA approves a contract rent up to the payment standard, subject to a
    *rent-reasonableness* test against comparable units. In the low-income ZIPs
    these deals live in, PHAs routinely approve at/near the payment standard
    even when an AVM "market rent" prints lower.
  - The tenant pays ~30% of adjusted income (their Total Tenant Payment); the
    PHA pays the rest -- the Housing Assistance Payment (HAP) -- directly to the
    landlord, on time, every month, regardless of the tenant's job situation.
    That guaranteed HAP portion is the income stability the strategy is after.

This module is pure arithmetic over numbers you feed it. The `re section8`
verb wires it to live data (lookup for the unit mix + ZIP, rent-estimate for
market rent, fmr.py for the FMRs).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

FMR_MAX_BEDS = 4  # HUD FMR tables top out at 4BR; 4 means "4 or more".
_BED_LABEL = {0: "Studio", 1: "1BR", 2: "2BR", 3: "3BR", 4: "4BR"}
_PREMIUM_BAND = 0.05  # +/-5% around market => "parity"


def _clamp_beds(beds: int) -> int:
    return max(0, min(FMR_MAX_BEDS, int(beds)))


def _bed_label(beds: int) -> str:
    b = _clamp_beds(beds)
    return _BED_LABEL[b] + ("+" if beds and int(beds) > FMR_MAX_BEDS else "")


def analyze(
    *,
    units: int,
    beds_per_unit: int,
    market_rent_total_monthly: float,
    fmr_by_beds: dict[int, int],
    payment_standard_pct: float = 1.0,
    utility_allowance_per_unit: float = 0.0,
    beds_assumed: bool = False,
    fmr_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compare Section 8 voucher income against open-market rent.

    All rents are monthly dollars. `fmr_by_beds` maps bedroom count -> FMR
    (from fmr.py). `market_rent_total_monthly` is the open-market rent across
    ALL units. A uniform unit mix (every unit has `beds_per_unit` bedrooms) is
    assumed; pass the real per-unit figure when you know it.
    """
    units = max(1, int(units))
    b = _clamp_beds(beds_per_unit)
    fmr_unit = fmr_by_beds.get(b)
    if fmr_unit is None:
        return {
            "ok": False,
            "error": f"no FMR for {b}BR in the supplied schedule",
            "fmr_by_beds": fmr_by_beds,
        }
    fmr_unit = int(fmr_unit)

    market_per_unit = round(market_rent_total_monthly / units, 2)
    payment_standard_unit = round(fmr_unit * payment_standard_pct)
    # Gross rent (= contract rent + tenant-paid utility allowance) is what the
    # payment standard caps. If the landlord pays utilities the allowance ~ 0
    # and the contract rent == the payment standard.
    contract_ceiling_unit = max(0.0, payment_standard_unit - utility_allowance_per_unit)

    # Two honest framings of the achievable Section 8 contract rent:
    #   typical      -> up to the payment standard (what PHAs commonly approve in
    #                   the low-income ZIPs these deals live in)
    #   conservative -> capped at market by the rent-reasonableness test
    s8_typical_unit = round(contract_ceiling_unit)
    s8_conservative_unit = round(min(contract_ceiling_unit, market_per_unit))

    premium_unit = round(s8_typical_unit - market_per_unit, 2)
    premium_pct = round(premium_unit / market_per_unit, 4) if market_per_unit else None

    if premium_pct is None:
        classification = "unknown"
    elif premium_pct >= _PREMIUM_BAND:
        classification = "premium"
    elif premium_pct <= -_PREMIUM_BAND:
        classification = "discount"
    else:
        classification = "parity"

    income_stability = "high" if classification in ("premium", "parity") else "medium"

    caveats: list[str] = []
    if beds_assumed:
        caveats.append(
            f"Bedroom count per unit was assumed ({b}BR). Confirm the real unit mix -- "
            "FMR is set per bedroom size, so this drives the whole comparison."
        )
    caveats.append(
        f"Payment standard modeled as {int(round(payment_standard_pct * 100))}% of FMR "
        "(PHAs set the real figure at 90-110%; there is no free per-PHA feed)."
    )
    caveats.append(
        "Section 8 'typical' assumes the PHA approves up to the payment standard; "
        "'conservative' applies the rent-reasonableness cap at market rent."
    )
    if utility_allowance_per_unit:
        caveats.append(
            f"A ${utility_allowance_per_unit:.0f}/unit utility allowance was netted out "
            "of the payment standard to get the landlord's contract rent."
        )
    else:
        caveats.append(
            "Assumes tenant-paid utilities (no allowance netted out); if the landlord "
            "pays utilities, the achievable contract rent is lower."
        )

    return {
        "ok": True,
        "classification": classification,  # premium | parity | discount
        "income_stability": income_stability,  # high | medium
        "units": units,
        "beds_per_unit": b,
        "beds_label": _bed_label(beds_per_unit),
        "payment_standard_pct": payment_standard_pct,
        "per_unit": {
            "market_rent": market_per_unit,
            "fmr": fmr_unit,
            "payment_standard": payment_standard_unit,
            "section8_typical": s8_typical_unit,
            "section8_conservative": s8_conservative_unit,
            "premium_vs_market": premium_unit,
            "premium_pct": premium_pct,
        },
        "totals": {
            "market_rent": round(market_rent_total_monthly, 2),
            "fmr": fmr_unit * units,
            "payment_standard": payment_standard_unit * units,
            "section8_typical": s8_typical_unit * units,
            "section8_conservative": s8_conservative_unit * units,
            "premium_vs_market": round(premium_unit * units, 2),
            "premium_pct": premium_pct,
        },
        "fmr_meta": fmr_meta or {},
        "caveats": caveats,
    }


def _money(v: Any) -> str:
    try:
        return f"${float(v):,.0f}"
    except (TypeError, ValueError):
        return "—"


def _signed_money(v: Any) -> str:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return "—"
    return f"+{_money(f)}" if f >= 0 else f"-{_money(abs(f))}"


def _signed_pct(v: Any) -> str:
    if v is None:
        return "—"
    return f"+{v * 100:.0f}%" if v >= 0 else f"{v * 100:.0f}%"


_VERDICT = {
    "premium": "Section 8 pays **above** open-market rent here -- the voucher is the better tenant economically, and the income is government-backed.",
    "parity": "Section 8 pays **about the same** as open-market rent -- take the voucher for the income stability at no rent give-up.",
    "discount": "Section 8 caps **below** open-market rent here -- a market tenant pays more; the voucher trades some rent for stability.",
    "unknown": "Could not classify Section 8 vs market (missing market rent).",
}


def render_markdown(res: dict[str, Any]) -> str:
    """Render the Section 8 dossier section body (no `## heading`)."""
    if not res.get("ok"):
        return f"Section 8 analysis unavailable: {res.get('error', 'unknown error')}\n"
    pu = res["per_unit"]
    tt = res["totals"]
    units = res["units"]
    label = res["beds_label"]
    meta = res.get("fmr_meta") or {}

    out: list[str] = [_VERDICT.get(res["classification"], "")]
    src_bits = [
        b
        for b in (
            meta.get("area_name"),
            f"FY{meta['fiscal_year']} FMR" if meta.get("fiscal_year") else None,
            f"via {meta['source']}" if meta.get("source") else None,
        )
        if b
    ]
    if src_bits:
        out.append(
            f"_{' · '.join(src_bits)} · {units} unit(s) @ {label} · "
            f"payment standard {int(round(res['payment_standard_pct'] * 100))}% of FMR_"
        )

    out.append("")
    out.append(f"| Rent (monthly) | Per unit | Total ({units} units) |")
    out.append("|---|---|---|")
    out.append(
        f"| Open-market rent | {_money(pu['market_rent'])} | {_money(tt['market_rent'])} |"
    )
    out.append(
        f"| HUD Fair Market Rent ({label}) | {_money(pu['fmr'])} | {_money(tt['fmr'])} |"
    )
    out.append(
        f"| Payment standard | {_money(pu['payment_standard'])} | {_money(tt['payment_standard'])} |"
    )
    out.append(
        f"| **Section 8 rent (typical)** | **{_money(pu['section8_typical'])}** | **{_money(tt['section8_typical'])}** |"
    )
    out.append(
        f"| Section 8 rent (conservative) | {_money(pu['section8_conservative'])} | {_money(tt['section8_conservative'])} |"
    )
    out.append(
        f"| Section 8 vs market | {_signed_money(pu['premium_vs_market'])} ({_signed_pct(pu['premium_pct'])}) | {_signed_money(tt['premium_vs_market'])} |"
    )
    out.append("")

    out.append(
        f"**Income stability: {res['income_stability'].upper()}.** Under a voucher the PHA "
        "pays the Housing Assistance Payment (HAP) portion directly to the landlord every "
        "month, on time, regardless of the tenant's employment; the tenant pays ~30% of "
        "adjusted income. Vouchers are scarce, so voucher tenants tend to stay -- lower "
        "turnover and vacancy than a market tenant. The trade-offs: an annual HQS inspection, "
        "a slower initial lease-up, and the payment-standard cap."
    )
    out.append("")
    out.append("**Caveats.**")
    out.extend(f"- {c}" for c in res.get("caveats", []))
    return "\n".join(out) + "\n"


def analyze_address(
    address: str,
    *,
    units: int = 1,
    beds_per_unit: int | None = None,
    market_rent_total: float | None = None,
    zip_code: str | None = None,
    payment_standard_pct: float = 1.0,
    utility_allowance: float = 0.0,
    year: int | None = None,
    hud_token: str | None = None,
    radius_miles: float = 1.0,
    max_radius_miles: float = 2.0,
    target_comp_count: int = 40,
    beds_tolerance: int = 0,
) -> dict[str, Any]:
    """Public wrapper to resolve address/ZIP and analyze Section 8 economics."""
    return _resolve(
        address=address,
        units=units,
        beds_per_unit=beds_per_unit,
        market_rent_total=market_rent_total,
        zip_code=zip_code,
        payment_standard_pct=payment_standard_pct,
        utility_allowance=utility_allowance,
        year=year,
        hud_token=hud_token,
        radius_miles=radius_miles,
        max_radius_miles=max_radius_miles,
        target_comp_count=target_comp_count,
        beds_tolerance=beds_tolerance,
    )


def _resolve(
    address: str,
    *,
    units: int,
    beds_per_unit: int | None,
    market_rent_total: float | None,
    zip_code: str | None,
    payment_standard_pct: float,
    utility_allowance: float,
    year: int | None,
    hud_token: str | None,
    radius_miles: float,
    max_radius_miles: float,
    target_comp_count: int,
    beds_tolerance: int,
) -> dict[str, Any]:
    """Wire live data sources to analyze(): resolve ZIP + unit mix + market rent."""
    import fmr

    agg: dict[str, Any] = {}
    beds_assumed = False
    notes: list[str] = []

    need_lookup = zip_code is None or beds_per_unit is None or market_rent_total is None
    clean_addr = address.strip()
    if zip_code is None and clean_addr.isdigit() and len(clean_addr) == 5:
        zip_code = clean_addr

    if need_lookup and not clean_addr.isdigit():
        import lookup

        lk = lookup.lookup(address)
        agg = lk.get("aggregate") or {}
        zip_code = zip_code or agg.get("zip")
        if beds_per_unit is None:
            total_beds = agg.get("beds")
            if total_beds and units:
                beds_per_unit = max(0, round(total_beds / units))
            else:
                beds_per_unit, beds_assumed = 2, True
    if beds_per_unit is None:
        beds_per_unit, beds_assumed = 2, True
    if zip_code is None:
        return {
            "ok": False,
            "error": "could not resolve a ZIP for this address; pass --zip",
        }

    if market_rent_total is None:
        import rent_estimate

        est = rent_estimate.estimate_rent(
            address,
            radius_miles=radius_miles,
            max_radius_miles=max_radius_miles,
            target_comp_count=target_comp_count,
            beds_tolerance=beds_tolerance,
        )
        market_rent_total = est.get("estimated_rent_mid")
        if market_rent_total is None:
            return {
                "ok": False,
                "error": "no market-rent comps; pass --market-rent-total or --rent-per-unit",
            }
        if units > 1:
            notes.append(
                "Market rent was auto-estimated from a whole-building comp set; for "
                "multifamily, prefer passing --rent-per-unit for a per-unit market rent."
            )

    fmr_res = fmr.lookup(zip_code, year=year, token=hud_token)
    if not fmr_res.get("ok"):
        return {
            "ok": False,
            "error": f"FMR lookup failed for {zip_code}: {fmr_res.get('error')}",
            "fmr_result": fmr_res,
        }

    res = analyze(
        units=units,
        beds_per_unit=beds_per_unit,
        market_rent_total_monthly=market_rent_total,
        fmr_by_beds={int(k): v for k, v in fmr_res["fmr"].items()},
        payment_standard_pct=payment_standard_pct,
        utility_allowance_per_unit=utility_allowance,
        beds_assumed=beds_assumed,
        fmr_meta={
            k: fmr_res.get(k)
            for k in ("area_name", "fiscal_year", "source", "zip", "is_small_area")
        },
    )
    if res.get("ok"):
        res["address"] = agg.get("address") or address
        res["zip"] = zip_code
        res["market_rent_total_input"] = round(float(market_rent_total), 2)
        if notes:
            res.setdefault("caveats", []).extend(notes)
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="section8", description="Section 8 voucher vs market-rent analysis"
    )
    ap.add_argument(
        "address",
        help="address (resolved for ZIP + unit mix) or a 5-digit ZIP with --rent-* set",
    )
    ap.add_argument("--units", type=int, default=2)
    ap.add_argument("--beds-per-unit", type=int)
    ap.add_argument(
        "--rent-per-unit",
        type=float,
        help="market rent per unit (skips the auto rent estimate)",
    )
    ap.add_argument(
        "--market-rent-total",
        type=float,
        help="market rent across all units (skips the auto rent estimate)",
    )
    ap.add_argument(
        "--zip", dest="zip_code", help="skip address lookup; use this ZIP for FMR"
    )
    ap.add_argument(
        "--payment-standard-pct",
        type=float,
        default=1.0,
        help="payment standard as a fraction of FMR (default 1.0)",
    )
    ap.add_argument(
        "--utility-allowance",
        type=float,
        default=0.0,
        help="tenant-paid utility allowance $/unit",
    )
    ap.add_argument(
        "--year", type=int, help="FMR fiscal year (default: latest available)"
    )
    ap.add_argument(
        "--hud-token",
        help="HUD API token (else uses the no-token bulk SAFMR file; also reads $HUD_API_TOKEN)",
    )
    ap.add_argument("--radius-miles", type=float, default=1.0)
    ap.add_argument("--max-radius-miles", type=float, default=3.0)
    ap.add_argument("--target-comps", dest="target_comp_count", type=int, default=40)
    ap.add_argument("--beds-tolerance", type=int, default=0)
    ap.add_argument(
        "--markdown",
        action="store_true",
        help="also print the rendered markdown section",
    )
    args = ap.parse_args(argv)

    market_total = args.market_rent_total
    if market_total is None and args.rent_per_unit is not None:
        market_total = args.rent_per_unit * args.units

    res = _resolve(
        args.address,
        units=args.units,
        beds_per_unit=args.beds_per_unit,
        market_rent_total=market_total,
        zip_code=args.zip_code,
        payment_standard_pct=args.payment_standard_pct,
        utility_allowance=args.utility_allowance,
        year=args.year,
        hud_token=args.hud_token or os.environ.get("HUD_API_TOKEN"),
        radius_miles=args.radius_miles,
        max_radius_miles=args.max_radius_miles,
        target_comp_count=args.target_comp_count,
        beds_tolerance=args.beds_tolerance,
    )
    json.dump(res, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")
    if args.markdown and res.get("ok"):
        sys.stdout.write("\n" + render_markdown(res))


if __name__ == "__main__":
    main()
