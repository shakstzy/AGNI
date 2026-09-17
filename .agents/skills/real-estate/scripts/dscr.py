#!/usr/bin/env python3
"""DSCR (Debt-Service Coverage Ratio) Loan Underwriting Engine.

Models real-world commercial non-QM DSCR financing for 1-4 unit residential
investment properties (the industry standard for remote small-multifamily investors).

Key DSCR Mechanics:
  - DSCR = Gross Monthly Rent / PITIA (Principal, Interest, Taxes, Insurance, HOA).
  - Lender DSCR Tiers (2026 Non-QM Benchmark Rates):
      Tier 1 (Optimal):    DSCR >= 1.25 -> 75-80% LTV, base rate ~7.50%
      Tier 2 (Standard):   1.15 <= DSCR < 1.25 -> 75% LTV, base rate ~7.875%
      Tier 3 (Acceptable): 1.00 <= DSCR < 1.15 -> 70% LTV, base rate ~8.25%
      Tier 4 (No-Ratio):   DSCR < 1.00 -> 65% LTV, base rate ~8.875% (+ reserves)
  - Loan Sizing Constraint:
      Approved Loan = min(Purchase Price * Max LTV, Max Loan supported by DSCR hurdle)
      If Gross Rent cannot support the desired LTV at target DSCR, loan amount is cut,
      requiring additional cash down payment.
  - Small Balance Hard Floor:
      National DSCR lenders enforce a minimum loan amount of $75,000 (many $100,000).
      Purchases below this floor cannot secure standard institutional DSCR paper and
      require portfolio bank debt, private lending (9.5%+), or all-cash execution.
  - Prepayment Penalties:
      Standard 3-2-1 or 5-4-3-2-1 stepdown prepay structure.
  - Liquid Reserves:
      6 to 12 months PITIA in verified post-closing liquidity.
  - Debt Yield:
      NOI / Loan Amount (standard hurdle >= 10.0%).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Any

DEFAULT_MIN_DSCR_HURDLE = 1.20
MIN_DSCR_LOAN_AMOUNT = 75000.0  # National institutional DSCR floor ($75k)
PREFERRED_LOAN_AMOUNT = 100000.0

TIER_GRID = [
    {
        "tier": "Tier 1 (Optimal)",
        "min_dscr": 1.25,
        "max_ltv": 0.80,
        "base_rate": 0.0750,
        "reserves_months": 6,
        "desc": "Prime non-QM DSCR: best pricing, maximum leverage up to 80% LTV",
    },
    {
        "tier": "Tier 2 (Standard)",
        "min_dscr": 1.15,
        "max_ltv": 0.75,
        "base_rate": 0.07875,
        "reserves_months": 6,
        "desc": "Standard investor DSCR: 1.15-1.24x coverage, 75% LTV ceiling",
    },
    {
        "tier": "Tier 3 (Sub-1.15)",
        "min_dscr": 1.00,
        "max_ltv": 0.70,
        "base_rate": 0.0825,
        "reserves_months": 9,
        "desc": "Tight debt service: 1.00-1.14x coverage, 70% LTV, higher liquidity reserves",
    },
    {
        "tier": "Tier 4 (No-Ratio)",
        "min_dscr": 0.0,
        "max_ltv": 0.65,
        "base_rate": 0.08875,
        "reserves_months": 12,
        "desc": "Deficit DSCR (<1.00x): max 65% LTV, 12 months post-closing reserves",
    },
]


def monthly_pi(loan: float, annual_rate: float, term_years: int = 30) -> float:
    """Calculate monthly amortized Principal & Interest payment."""
    if loan <= 0:
        return 0.0
    mr = annual_rate / 12.0
    n = term_years * 12
    if mr == 0:
        return loan / n
    return loan * (mr * (1 + mr) ** n) / ((1 + mr) ** n - 1)


def monthly_interest_only(loan: float, annual_rate: float) -> float:
    """Calculate monthly interest-only payment."""
    return (loan * annual_rate) / 12.0


def solve_max_loan_for_dscr(
    *,
    gross_rent_monthly: float,
    taxes_monthly: float,
    insurance_monthly: float,
    hoa_monthly: float,
    annual_rate: float,
    target_dscr: float,
    term_years: int = 30,
    interest_only: bool = False,
) -> float:
    """Calculate the maximum loan amount where Gross Rent / PITIA >= target_dscr."""
    max_pitia = gross_rent_monthly / target_dscr
    fixed_ti_a = taxes_monthly + insurance_monthly + hoa_monthly
    max_pi = max_pitia - fixed_ti_a
    if max_pi <= 0:
        return 0.0

    if interest_only:
        return (max_pi * 12.0) / annual_rate

    mr = annual_rate / 12.0
    n = term_years * 12
    factor = (mr * (1 + mr) ** n) / ((1 + mr) ** n - 1)
    return max_pi / factor


def underwrite_dscr(
    *,
    price: float,
    gross_rent_monthly: float,
    annual_taxes: float,
    annual_insurance: float,
    monthly_hoa: float = 0.0,
    target_ltv: float = 0.75,
    annual_rate: float | None = None,
    term_years: int = 30,
    product: str = "30yr-fixed",
    min_dscr_target: float = DEFAULT_MIN_DSCR_HURDLE,
    units: int = 2,
    origination_points: float = 1.5,
    underwriting_fees: float = 1495.0,
    appraisal_fee: float = 750.0,
    title_escrow_pct: float = 0.015,
) -> dict[str, Any]:
    """Underwrite a DSCR loan against investor standards and return full loan economics."""
    taxes_monthly = annual_taxes / 12.0
    insurance_monthly = annual_insurance / 12.0

    rate_adj = 0.0025 if units in (2, 3, 4) else 0.0
    if product == "5/1-arm":
        rate_adj -= 0.00375
    elif product == "interest-only":
        rate_adj += 0.0025

    trial_loan = round(price * target_ltv, 2)

    if annual_rate is None:
        prelim_rate = 0.07875 + rate_adj
        prelim_pi = (
            monthly_interest_only(trial_loan, prelim_rate)
            if product == "interest-only"
            else monthly_pi(trial_loan, prelim_rate, term_years)
        )
        prelim_pitia = prelim_pi + taxes_monthly + insurance_monthly + monthly_hoa
        prelim_dscr = round(gross_rent_monthly / prelim_pitia, 3) if prelim_pitia > 0 else 0.0

        active_tier = TIER_GRID[-1]
        for t in TIER_GRID:
            if prelim_dscr >= t["min_dscr"]:
                active_tier = t
                break
        effective_rate = round(active_tier["base_rate"] + rate_adj, 5)
    else:
        effective_rate = round(annual_rate + rate_adj, 5)
        active_tier = TIER_GRID[1]

    max_allowed_ltv = min(target_ltv, active_tier.get("max_ltv", 0.75))
    if units in (2, 3, 4) and max_allowed_ltv > 0.75:
        max_allowed_ltv = 0.75
    loan_by_ltv = round(price * max_allowed_ltv, 2)

    loan_by_dscr = round(
        solve_max_loan_for_dscr(
            gross_rent_monthly=gross_rent_monthly,
            taxes_monthly=taxes_monthly,
            insurance_monthly=insurance_monthly,
            hoa_monthly=monthly_hoa,
            annual_rate=effective_rate,
            target_dscr=min_dscr_target,
            term_years=term_years,
            interest_only=(product == "interest-only"),
        ),
        2,
    )

    final_loan = min(loan_by_ltv, loan_by_dscr)
    loan_cut_for_dscr = final_loan < loan_by_ltv
    dscr_cut_amount = round(loan_by_ltv - final_loan, 2) if loan_cut_for_dscr else 0.0

    clears_min_loan = final_loan >= MIN_DSCR_LOAN_AMOUNT
    loan_size_flag = "qualified" if clears_min_loan else "below_floor_disqualified"

    final_pi = (
        monthly_interest_only(final_loan, effective_rate)
        if product == "interest-only"
        else monthly_pi(final_loan, effective_rate, term_years)
    )
    final_pitia = round(final_pi + taxes_monthly + insurance_monthly + monthly_hoa, 2)
    actual_dscr = round(gross_rent_monthly / final_pitia, 3) if final_pitia > 0 else 0.0

    down_payment = round(price - final_loan, 2)
    down_pct = round(down_payment / price, 4) if price else 0.0
    points_fee = round(final_loan * (origination_points / 100.0), 2)
    title_closing_costs = round(price * title_escrow_pct, 2)
    total_lender_fees = round(points_fee + underwriting_fees + appraisal_fee, 2)
    total_cash_to_close = round(down_payment + total_lender_fees + title_closing_costs, 2)

    reserves_months = active_tier.get("reserves_months", 6)
    liquid_reserves_required = round(final_pitia * reserves_months, 2)
    total_liquidity_required = round(total_cash_to_close + liquid_reserves_required, 2)

    estimated_noi_annual = (gross_rent_monthly * 12.0 * 0.50)
    debt_yield = round((estimated_noi_annual / final_loan) * 100, 2) if final_loan > 0 else 0.0

    prepay_schedules = {
        "standard_3_2_1": "3% Yr 1, 2% Yr 2, 1% Yr 3, 0% thereafter",
        "institutional_5_4_3_2_1": "5% Yr 1, 4% Yr 2, 3% Yr 3, 2% Yr 4, 1% Yr 5",
        "soft_prepay": "1% rate premium or +0.25% note rate to eliminate prepay",
    }

    notes = []
    if not clears_min_loan:
        notes.append(
            f"DISQUALIFIED: Approved loan (${final_loan:,.0f}) is below the institutional "
            f"DSCR minimum floor (${MIN_DSCR_LOAN_AMOUNT:,.0f}). Requires small-balance portfolio "
            "lender (rate 9.5%+ / 3-4 pts), blanket mortgage, or cash purchase."
        )
    if loan_cut_for_dscr:
        notes.append(
            f"LOAN CUT: Rent (${gross_rent_monthly:,.0f}/mo) failed {min_dscr_target:.2f}x DSCR at "
            f"{max_allowed_ltv*100:.0f}% LTV. Loan trimmed by ${dscr_cut_amount:,.0f}. "
            f"Down payment increased from ${price - loan_by_ltv:,.0f} to ${down_payment:,.0f} ({down_pct*100:.1f}%)."
        )
    if actual_dscr >= 1.25:
        notes.append("Optimal coverage (>=1.25x): qualifies for prime rate tier and streamlined lender approval.")
    elif actual_dscr >= 1.00:
        notes.append("Acceptable coverage (1.00x - 1.24x): subject to rate adjustments and tighter reserve requirements.")
    else:
        notes.append("Deficit DSCR (<1.00x): requires no-ratio program, 35% down, and 12 months verified liquid reserves.")

    return {
        "ok": True,
        "price": price,
        "units": units,
        "product": product,
        "term_years": term_years,
        "interest_rate": effective_rate,
        "interest_rate_pct": round(effective_rate * 100, 3),
        "target_ltv": target_ltv,
        "actual_ltv": round(final_loan / price, 4) if price else 0.0,
        "loan_amount": final_loan,
        "loan_by_ltv": loan_by_ltv,
        "loan_by_dscr": loan_by_dscr,
        "loan_cut_for_dscr": loan_cut_for_dscr,
        "dscr_cut_amount": dscr_cut_amount,
        "clears_min_loan_floor": clears_min_loan,
        "min_loan_floor": MIN_DSCR_LOAN_AMOUNT,
        "loan_size_status": loan_size_flag,
        "tier": active_tier["tier"],
        "dscr": actual_dscr,
        "min_dscr_target": min_dscr_target,
        "pitia_monthly": final_pitia,
        "breakdown": {
            "principal_interest_monthly": round(final_pi, 2),
            "taxes_monthly": round(taxes_monthly, 2),
            "insurance_monthly": round(insurance_monthly, 2),
            "hoa_monthly": round(monthly_hoa, 2),
            "gross_rent_monthly": round(gross_rent_monthly, 2),
        },
        "closing_costs": {
            "down_payment": down_payment,
            "down_payment_pct": down_pct,
            "origination_points": origination_points,
            "points_fee": points_fee,
            "underwriting_fees": underwriting_fees,
            "appraisal_fee": appraisal_fee,
            "title_escrow_closing": title_closing_costs,
            "total_cash_to_close": total_cash_to_close,
        },
        "reserves": {
            "months_required": reserves_months,
            "liquid_reserves_required": liquid_reserves_required,
            "total_liquidity_needed": total_liquidity_required,
        },
        "debt_yield_pct": debt_yield,
        "prepay_structure": prepay_schedules["standard_3_2_1"],
        "notes": notes,
    }


def render_markdown(d: dict[str, Any]) -> str:
    lines = []
    lines.append("### DSCR Loan Financing Schedule")
    lines.append("")
    status_icon = "✅ QUALIFIED" if d["clears_min_loan_floor"] else "⚠️ DISQUALIFIED (<$75k floor)"
    lines.append(f"**Status:** {status_icon} · **DSCR:** {d["dscr"]:.2f}x · **Rate:** {d["interest_rate_pct"]:.3f}% ({d["product"]}) · **LTV:** {d["actual_ltv"]*100:.1f}%")
    lines.append("")
    lines.append("| DSCR Underwriting Metric | Value | Underwriter Standard / Constraint |")
    lines.append("|---|---|---|")
    lines.append(f"| **Purchase Price** | ${d["price"]:,.0f} | Contract acquisition price |")
    lines.append(f"| **Approved Loan Amount** | ${d["loan_amount"]:,.0f} | Lesser of {d["target_ltv"]*100:.0f}% LTV (${d["loan_by_ltv"]:,.0f}) or {d["min_dscr_target"]:.2f}x DSCR cap (${d["loan_by_dscr"]:,.0f}) |")
    lines.append(f"| **Down Payment** | ${d["closing_costs"]["down_payment"]:,.0f} ({d["closing_costs"]["down_payment_pct"]*100:.1f}%) | Equity required at purchase |")
    lines.append(f"| **Interest Rate** | {d["interest_rate_pct"]:.3f}% | 2026 Non-QM benchmark (includes 2-4 unit spread) |")
    lines.append(f"| **Monthly P&I** | ${d["breakdown"]["principal_interest_monthly"]:,.2f} | 30-year amortized debt service |")
    lines.append(f"| **Monthly Taxes & Ins.** | ${d["breakdown"]["taxes_monthly"] + d["breakdown"]["insurance_monthly"]:,.2f} | Escrowed holding costs |")
    lines.append(f"| **Total PITIA** | **${d["pitia_monthly"]:,.2f}/mo** | Total qualifying debt service |")
    lines.append(f"| **Qualifying DSCR** | **{d["dscr"]:.2f}x** | Minimum hurdle: {d["min_dscr_target"]:.2f}x (Tier: {d["tier"]}) |")
    lines.append(f"| **Estimated Debt Yield** | {d["debt_yield_pct"]:.2f}% | Hurdle >= 9.5-10.0% |")
    lines.append(f"| **Lender Points & Fees** | ${d["closing_costs"]["points_fee"] + d["closing_costs"]["underwriting_fees"] + d["closing_costs"]["appraisal_fee"]:,.0f} | {d["closing_costs"]["origination_points"]:.1f} pts + underwriting + appraisal |")
    lines.append(f"| **Total Cash to Close** | **${d["closing_costs"]["total_cash_to_close"]:,.0f}** | Down payment + points + title & escrow |")
    lines.append(f"| **Required Liquid Reserves** | ${d["reserves"]["liquid_reserves_required"]:,.0f} | {d["reserves"]["months_required"]} months verified PITIA post-closing |")
    lines.append(f"| **Prepayment Penalty** | {d["prepay_structure"]} | Stepdown buyout penalty |")
    lines.append("")
    if d.get("notes"):
        lines.append("**Underwriting Notes:**")
        for n in d["notes"]:
            lines.append(f"- {n}")
        lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="DSCR Loan Underwriting Calculator")
    parser.add_argument("price", type=float, help="Property purchase price")
    parser.add_argument("--rent", type=float, required=True, help="Gross monthly rental income")
    parser.add_argument("--taxes", type=float, required=True, help="Annual property taxes")
    parser.add_argument("--insurance", type=float, default=1200.0, help="Annual hazard insurance")
    parser.add_argument("--hoa", type=float, default=0.0, help="Monthly HOA fee")
    parser.add_argument("--ltv", type=float, default=0.75, help="Target LTV (e.g. 0.75 or 0.80)")
    parser.add_argument("--rate", type=float, default=None, help="Explicit annual interest rate (e.g. 0.07875)")
    parser.add_argument("--units", type=int, default=2, help="Number of residential units (1-4)")
    parser.add_argument("--product", choices=["30yr-fixed", "5/1-arm", "interest-only"], default="30yr-fixed")
    parser.add_argument("--min-dscr", type=float, default=1.20, help="Minimum qualifying DSCR threshold")
    parser.add_argument("--markdown", action="store_true", help="Render output as Markdown")

    args = parser.parse_args()
    res = underwrite_dscr(
        price=args.price,
        gross_rent_monthly=args.rent,
        annual_taxes=args.taxes,
        annual_insurance=args.insurance,
        monthly_hoa=args.hoa,
        target_ltv=args.ltv,
        annual_rate=args.rate,
        units=args.units,
        product=args.product,
        min_dscr_target=args.min_dscr,
    )

    if args.markdown:
        print(render_markdown(res))
    else:
        print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
