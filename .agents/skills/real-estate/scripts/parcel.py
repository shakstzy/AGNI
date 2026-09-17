#!/usr/bin/env python3
"""Parcel-by-Parcel Intelligence Engine for Real Estate Acquisitions.

Extracts, enriches, and models deep property parcel characteristics:
  1. Cadastral & Tax Assessor: APN, county, assessed value, post-sale tax reassessment shock.
  2. Physical Lot & Spatial Geometry: lot size/acres, lot dimensions, lot position (cul-de-sac, corner, interior), backs_to (park, alley, rail).
  3. Zoning & Density: zoning code (2F, MF, R-1), legal conforming status, ADU feasibility.
  4. FEMA Flood & Environmental: Flood zone (X vs A/AE), SFHA flag, mandatory flood insurance cost impact.
  5. Mechanical & Metering Stack: Separate electric/gas meters, 100A/200A panels, knob-and-tube detection, lead-safe pre-1978 compliance.
  6. Unit-by-Unit Mix: Individual unit breakdown for multi-family assets.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any


def analyze_parcel(
    *,
    address: str,
    price: float | None = None,
    lot_sqft: float | None = None,
    year_built: int | None = None,
    property_type: str | None = None,
    units: int = 1,
    beds: int | None = None,
    baths: float | None = None,
    sqft: float | None = None,
    tax_assessed_value: float | None = None,
    historical_annual_tax: float | None = None,
    property_tax_rate: float | None = None,
    effective_tax_rate: float = 0.023,  # Typical Cuyahoga / Midwest effective rate (2.3%)
    apn: str | None = None,
    zoning: str | None = None,
    flood_zone: str | None = None,
    lot_position: str | None = None,
    backs_to: str | None = None,
    description_text: str | None = None,
) -> dict[str, Any]:
    """Analyze complete parcel-by-parcel attributes and risks."""
    text_corpus = (description_text or "").lower()

    # 1. Lot Spatial & Physical Geometry
    acres = round(lot_sqft / 43560.0, 3) if lot_sqft else None

    # Infer lot position if not explicitly supplied
    inferred_position = lot_position or "interior_lot"
    if not lot_position:
        if "cul-de-sac" in text_corpus or "cul de sac" in text_corpus:
            inferred_position = "cul_de_sac"
        elif "corner lot" in text_corpus or "corner" in address.lower():
            inferred_position = "corner_lot"
        elif "flag lot" in text_corpus:
            inferred_position = "flag_lot"

    # Infer rear boundary exposure
    inferred_backs_to = backs_to or "residential_neighbor"
    if not backs_to:
        if any(w in text_corpus for w in ["backs to park", "wooded", "greenbelt", "ravine", "private backyard"]):
            inferred_backs_to = "greenbelt_park"
        elif any(w in text_corpus for w in ["alley access", "rear alley", "paved alley"]):
            inferred_backs_to = "alley"
        elif any(w in text_corpus for w in ["railroad", "tracks", "train"]):
            inferred_backs_to = "railroad"
        elif any(w in text_corpus for w in ["commercial", "shopping", "retail", "plaza"]):
            inferred_backs_to = "commercial"

    # Approximate lot dimensions from sqft (assuming standard 3:1 depth to width ratio)
    estimated_frontage_ft = round((lot_sqft / 3.0) ** 0.5, 1) if lot_sqft else None
    estimated_depth_ft = round(estimated_frontage_ft * 3.0, 1) if estimated_frontage_ft else None

    # 2. Cadastral & Post-Sale Tax Reassessment Shock
    tax_rate = (
        (property_tax_rate / 100.0)
        if (property_tax_rate and property_tax_rate > 0.1)
        else (property_tax_rate or effective_tax_rate or 0.023)
    )

    if historical_annual_tax is not None and historical_annual_tax > 0:
        historical_tax_annual = round(float(historical_annual_tax), 2)
    elif tax_assessed_value:
        # Check if tax_assessed_value looks like fractional statutory assessed value (e.g. Ohio 35%, Michigan 50% SEV)
        # vs full market value.
        ratio = (tax_assessed_value / price) if price and price > 0 else 0.35
        if ratio <= 0.40:
            est_market_val = tax_assessed_value / 0.35  # Ohio 35% statutory assessment standard
        elif ratio <= 0.55:
            est_market_val = tax_assessed_value / 0.50  # Michigan 50% SEV standard
        else:
            est_market_val = tax_assessed_value
        historical_tax_annual = round(est_market_val * tax_rate, 2)
    else:
        historical_tax_annual = round((price * 0.75 if price else 0.0) * tax_rate, 2)
    historical_tax_monthly = round(historical_tax_annual / 12.0, 2)

    # Projected reassessed taxes based on purchase price (Ohio / Midwest Auditor Reassessment)
    purchase_price = price or (tax_assessed_value / 0.35 if tax_assessed_value else 0.0)
    projected_tax_annual = round(purchase_price * tax_rate, 2)
    projected_tax_monthly = round(projected_tax_annual / 12.0, 2)

    tax_shock_annual = round(max(0.0, projected_tax_annual - historical_tax_annual), 2)
    tax_shock_monthly = round(tax_shock_annual / 12.0, 2)

    # 3. Zoning & Density Classification
    resolved_zoning = zoning
    if not resolved_zoning:
        if units >= 2 or "multi" in str(property_type).lower():
            resolved_zoning = "2F (Two-Family Residential)" if units == 2 else "MF (Multi-Family Residential)"
        else:
            resolved_zoning = "R-1 (Single-Family Residential)"

    legal_conforming = True
    if units >= 2 and "R-1" in resolved_zoning:
        legal_conforming = False  # Grandfathered non-conforming risk

    adu_potential = "High" if (lot_sqft and lot_sqft >= 6000 and units == 1) else "Restricted"

    # 4. FEMA Flood Zone & Environmental Hazards
    resolved_flood = (flood_zone or "X").upper()
    is_sfha = resolved_flood in ("A", "AE", "AH", "AO", "VE", "V")
    mandatory_flood_insurance = is_sfha
    flood_insurance_annual = 2100.0 if is_sfha else 0.0
    flood_insurance_monthly = round(flood_insurance_annual / 12.0, 2)

    # 5. Mechanical & Infrastructure Stack
    separate_electric = (units > 1) and not any(w in text_corpus for w in ["master electric", "shared electric", "one meter"])
    separate_gas = (units > 1) and not any(w in text_corpus for w in ["boiler", "steam heat", "master gas", "radiator"])
    separate_water = any(w in text_corpus for w in ["separate water", "submetered water"])

    # Pre-1978 lead paint and NSPIRE risk
    lead_paint_risk = (year_built is not None and year_built < 1978)
    knob_and_tube_risk = (year_built is not None and year_built < 1940)

    # 6. Unit-by-Unit Mix Decomposition
    unit_list = []
    if units == 1:
        unit_list.append({
            "unit_name": "Main Single Family",
            "beds": beds or 3,
            "baths": baths or 1.0,
            "sqft": sqft or 1200,
            "metering": "Single Tenant Paid",
        })
    else:
        total_b = beds or (units * 2)
        total_ba = baths or (units * 1.0)
        total_sqft = sqft or (units * 900)

        base_b = total_b // units
        rem_b = total_b % units
        base_ba = round(total_ba / units, 1)
        base_sqft = round(total_sqft / units, 0)

        for i in range(units):
            u_beds = base_b + (1 if i < rem_b else 0)
            unit_list.append({
                "unit_name": f"Unit {i+1} ({chr(65+i)})",
                "beds": u_beds,
                "baths": base_ba,
                "sqft": base_sqft,
                "metering": "Separate Electric/Gas" if (separate_electric and separate_gas) else "Master Metered",
            })

    # Parcel score adjustments
    parcel_score_adj = 0
    if inferred_position == "cul_de_sac":
        parcel_score_adj += 5
    elif inferred_position == "corner_lot":
        parcel_score_adj -= 2
    if inferred_backs_to == "greenbelt_park":
        parcel_score_adj += 5
    elif inferred_backs_to in ("railroad", "commercial"):
        parcel_score_adj -= 10
    if is_sfha:
        parcel_score_adj -= 25
    if not legal_conforming:
        parcel_score_adj -= 15

    return {
        "ok": True,
        "address": address,
        "apn": apn or "Assessor APN on File",
        "cadastral": {
            "tax_assessed_value": tax_assessed_value,
            "purchase_price": purchase_price,
            "effective_tax_rate": tax_rate,
            "historical_tax_annual": historical_tax_annual,
            "historical_tax_monthly": historical_tax_monthly,
            "projected_reassessed_tax_annual": projected_tax_annual,
            "projected_reassessed_tax_monthly": projected_tax_monthly,
            "tax_shock_annual": tax_shock_annual,
            "tax_shock_monthly": tax_shock_monthly,
        },
        "site": {
            "lot_sqft": lot_sqft,
            "lot_acres": acres,
            "estimated_dimensions": f"{estimated_frontage_ft} ft x {estimated_depth_ft} ft" if estimated_frontage_ft else "Unknown",
            "lot_position": inferred_position,
            "backs_to": inferred_backs_to,
        },
        "zoning": {
            "classification": resolved_zoning,
            "units": units,
            "legal_conforming": legal_conforming,
            "adu_potential": adu_potential,
        },
        "flood": {
            "zone": resolved_flood,
            "is_sfha": is_sfha,
            "mandatory_flood_insurance": mandatory_flood_insurance,
            "flood_insurance_annual": flood_insurance_annual,
            "flood_insurance_monthly": flood_insurance_monthly,
        },
        "mechanics": {
            "year_built": year_built,
            "separate_electric": separate_electric,
            "separate_gas": separate_gas,
            "separate_water": separate_water,
            "lead_paint_risk": lead_paint_risk,
            "knob_and_tube_risk": knob_and_tube_risk,
        },
        "units": unit_list,
        "score_adjustment": parcel_score_adj,
    }


def render_markdown(d: dict[str, Any]) -> str:
    lines = []
    lines.append(f"### Parcel Intelligence: {d['address']}")
    lines.append("")
    cad = d["cadastral"]
    site = d["site"]
    zon = d["zoning"]
    fld = d["flood"]
    mech = d["mechanics"]

    lines.append("| Parcel Dimension | Specification | Underwriter Assessment / Impact |")
    lines.append("|---|---|---|")
    lines.append(f"| **APN / Tax ID** | `{d['apn']}` | County Cadastral Identifier |")
    lot_str = f"{site['lot_sqft']:,.0f} sqft ({site['lot_acres']:.3f} ac)" if site['lot_sqft'] else "Unknown"
    lines.append(f"| **Lot Size & Geometry** | {lot_str} | Approx. dimensions: {site['estimated_dimensions']} |")
    lines.append(f"| **Lot Position** | `{site['lot_position']}` | Rear exposure: `{site['backs_to']}` |")
    conf_str = "✅ Conforming" if zon['legal_conforming'] else "⚠️ Non-conforming grandfathered"
    lines.append(f"| **Zoning & Density** | {zon['classification']} | Conforming: {conf_str} · ADU: {zon['adu_potential']} |")

    flood_status = "✅ Zone X (Minimal Risk)" if not fld["is_sfha"] else f"🚨 {fld['zone']} SFHA (+$175/mo mandatory insurance)"
    ins_str = "YES" if fld['mandatory_flood_insurance'] else "NO"
    lines.append(f"| **FEMA Flood Hazard** | {flood_status} | Mandatory flood insurance: {ins_str} |")

    reassess_flag = f"⚠️ +${cad['tax_shock_monthly']:,.0f}/mo shock" if cad["tax_shock_monthly"] > 25 else "Nominal change"
    lines.append(f"| **Post-Sale Tax Reassessment** | ${cad['historical_tax_monthly']:,.0f}/mo -> **${cad['projected_reassessed_tax_monthly']:,.0f}/mo** | {reassess_flag} (${cad['projected_reassessed_tax_annual']:,.0f}/yr based on purchase price) |")

    elec_status = "Separate tenant meters" if mech["separate_electric"] else "Master metered (Landlord pays)"
    gas_status = "Separate furnaces" if mech["separate_gas"] else "Central boiler (Landlord pays)"
    water_str = "Sub-metered" if mech['separate_water'] else "Master meter (Landlord lien liability)"
    lines.append(f"| **Utility Metering Stack** | Electric: {elec_status} · Gas: {gas_status} | Water: {water_str} |")

    lead_status = "⚠️ Pre-1978 build: Mandatory Lead-Safe inspection ($500)" if mech["lead_paint_risk"] else "✅ Post-1978 build"
    lines.append(f"| **Environmental / Year Built** | Built in {mech['year_built'] or 'Unknown'} | {lead_status} |")
    lines.append("")

    lines.append("**Unit-by-Unit Configuration:**")
    lines.append("")
    lines.append("| Unit | Beds / Baths | Approx Sqft | Metering Configuration |")
    lines.append("|---|---|---|---|")
    for u in d["units"]:
        lines.append(f"| {u['unit_name']} | {u['beds']} bed / {u['baths']} bath | {u['sqft']:,.0f} sqft | {u['metering']} |")
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Parcel-by-Parcel Intelligence Analyzer")
    parser.add_argument("address", help="Property street address")
    parser.add_argument("--price", type=float, help="Purchase price")
    parser.add_argument("--lot-sqft", type=float, default=5200.0, help="Lot square footage")
    parser.add_argument("--year-built", type=int, default=1920, help="Year built")
    parser.add_argument("--units", type=int, default=2, help="Unit count")
    parser.add_argument("--beds", type=int, default=4, help="Total beds")
    parser.add_argument("--baths", type=float, default=2.0, help="Total baths")
    parser.add_argument("--sqft", type=float, default=2000.0, help="Total living square feet")
    parser.add_argument("--tax-assessed", type=float, help="Current tax assessed value")
    parser.add_argument("--annual-tax", type=float, help="Historical annual property tax paid")
    parser.add_argument("--effective-tax-rate", type=float, help="Effective property tax rate (e.g. 0.023)")
    parser.add_argument("--flood-zone", choices=["X", "AE", "A", "AO", "VE"], default="X")
    parser.add_argument("--markdown", action="store_true", help="Render output as Markdown")

    args = parser.parse_args()

    # If key details are omitted, attempt lookup to populate real property attributes
    if args.price is None:
        try:
            import lookup
            lk = lookup.lookup(args.address)
            agg = lk.get("aggregate") or {}
            args.price = args.price or agg.get("price")
            args.lot_sqft = agg.get("lot_size") or agg.get("lot_sqft") or args.lot_sqft
            args.year_built = agg.get("year_built") or args.year_built
            args.beds = agg.get("beds") or args.beds
            args.baths = agg.get("baths") or args.baths
            args.sqft = agg.get("sqft") or args.sqft
            args.tax_assessed = agg.get("tax_assessed_value") or args.tax_assessed
            if agg.get("annual_property_tax") and not args.annual_tax:
                args.annual_tax = float(agg["annual_property_tax"])
        except Exception:
            pass

    res = analyze_parcel(
        address=args.address,
        price=args.price,
        lot_sqft=args.lot_sqft,
        year_built=args.year_built,
        units=args.units,
        beds=args.beds,
        baths=args.baths,
        sqft=args.sqft,
        tax_assessed_value=args.tax_assessed,
        historical_annual_tax=args.annual_tax,
        effective_tax_rate=args.effective_tax_rate or 0.023,
        flood_zone=args.flood_zone,
    )

    if args.markdown:
        print(render_markdown(res))
    else:
        print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
