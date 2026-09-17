#!/usr/bin/env python3
"""Capital-efficient deal recommendation engine based on a sliding budget.

Recommends the best in-budget property and discovers asymmetric stretch
opportunities where investing a slightly larger amount delivers dramatically
higher return percentages (Cash-on-Cash %) or aggressive marginal ROI.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

# Ensure workspace and skill paths are in sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = SCRIPT_DIR.parents[4] / "workspaces" / "real-estate"
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(WORKSPACE_DIR / "scripts"))

import repo
import run


def load_properties_for_market(market: str) -> list[dict]:
    """Load indexed property records for a given market."""
    index_path = WORKSPACE_DIR / "raw" / "index.jsonl"
    if not index_path.exists():
        return []
    idx = repo.load_index(str(index_path))
    return [
        r for r in idx.values()
        if (r.get("market") == market or market == "all")
    ]


def format_money(v: Any) -> str:
    return f"${v:,.0f}" if isinstance(v, (int, float)) else "—"


def format_pct(v: Any) -> str:
    return f"{v:.1f}%" if isinstance(v, (int, float)) else "—"


def render_recommendation_cli(rec_analysis: dict, market: str) -> str:
    """Format an executive terminal summary for the user."""
    b = rec_analysis["budget"]
    s_ceil = rec_analysis["stretch_ceiling"]
    s_win = rec_analysis["stretch_window"]

    lines = []
    lines.append(f"================================================================================")
    lines.append(f"  CAPITAL ALLOCATION ENGINE — {market.upper()}")
    lines.append(f"  Sliding Budget: {format_money(b)}  |  Stretch Window: +{format_money(s_win)} (Up to {format_money(s_ceil)})")
    lines.append(f"================================================================================")
    lines.append("")

    bib = rec_analysis.get("best_in_budget")
    if bib:
        bib_cf = (
            bib.get("dscr_cash_flow_monthly")
            if bib.get("dscr_cash_flow_monthly") is not None
            else (bib.get("market_cash_flow_monthly") or 0.0)
        )
        lines.append("🎯 TOP IN-BUDGET DEAL (Affordable Now)")
        lines.append(f"   Address:         {bib.get('address')}")
        lines.append(f"   Price:           {format_money(bib.get('price'))} ({bib.get('units') or 1} units)")
        lines.append(f"   Cash to Close:   {format_money(bib.get('_c2c'))}  (Remaining buffer: {format_money(b - bib.get('_c2c'))})")
        lines.append(f"   Net Cash Flow:   +{format_money(bib_cf)}/mo  ({format_money(float(bib_cf) * 12)}/yr)")
        lines.append(f"   Cash-on-Cash:    {format_pct(bib.get('_coc'))}")
        lines.append(f"   DSCR Coverage:   {bib.get('dscr_ratio', 0.0):.2f}x  |  Deal Score: {bib.get('_score', 0)}")
        lines.append("")
    else:
        lines.append(f"⚠️  No properties found under your budget of {format_money(b)}.")
        lines.append("")

    bs = rec_analysis.get("best_stretch")
    if bs:
        bs_deal = bs["deal"]
        lines.append("🚀 ASYMMETRIC STRETCH OPPORTUNITY (Higher Return Percentage)")
        lines.append(f"   💡 \"Hey, you're only {format_money(bs['gap_from_budget'])} away from being able to afford")
        lines.append(f"       {bs_deal.get('address')} as well, which increases your overall returns significantly!\"")
        lines.append("")
        lines.append(f"   • Capital Gap:             +{format_money(bs['gap_from_budget'])} over budget (Total Cash to Close: {format_money(bs_deal.get('_c2c'))})")
        lines.append(f"   • Return Acceleration:     Bumps Cash-on-Cash from {format_pct(bs['base_coc'])} ➔ {format_pct(bs['stretch_coc'])} (+{bs['coc_lift']:.1f}% yield lift)")
        lines.append(f"   • Cash Flow Expansion:     +{format_money(bs['stretch_cf_mo'])}/mo (+{format_money(bs['extra_cf_mo'])}/mo net increase, +{format_money(bs['extra_cf_annual'])}/yr)")
        lines.append(f"   • Return on Extra Capital: {format_pct(bs['marginal_coc'])} marginal cash return on the additional {format_money(bs['extra_capital_vs_base'])}!")
        lines.append(f"   • DSCR / Quality:          {bs_deal.get('dscr_ratio', 0.0):.2f}x  |  Score: {bs_deal.get('_score', 0)}")
        lines.append("")

    # Full table preview
    all_recs = sorted(
        rec_analysis.get("in_budget", []) + rec_analysis.get("stretch_pool", []),
        key=lambda r: r.get("_score", 0),
        reverse=True
    )
    if all_recs:
        lines.append("RANKED CAPITAL EFFICIENCY TABLE:")
        lines.append(f"{'#':<3} {'Address':<32} {'Price':<10} {'Cash Req':<10} {'CF/mo':<9} {'CoC %':<8} {'DSCR':<7} {'Status':<16}")
        lines.append("-" * 98)
        for i, r in enumerate(all_recs[:10], 1):
            c2c = r.get("_c2c", 0.0)
            coc = r.get("_coc", 0.0)
            cf = r.get("dscr_cash_flow_monthly") if r.get("dscr_cash_flow_monthly") is not None else (r.get("market_cash_flow_monthly") or 0.0)
            dscr_v = f"{r.get('dscr_ratio', 0.0):.2f}x"
            if c2c <= b:
                status = "🎯 In-Budget"
            elif c2c <= s_ceil:
                status = f"🚀 +{format_money(c2c - b)}"
            else:
                status = "Above Budget"
            addr = str(r.get("address", ""))[:30]
            lines.append(f"{i:<3} {addr:<32} {format_money(r.get('price')):<10} {format_money(c2c):<10} {format_money(cf):<9} {format_pct(coc):<8} {dscr_v:<7} {status:<16}")
        lines.append("")

    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="recommend", description="Budget-aware deal recommendation & capital optimization engine")
    ap.add_argument("market", nargs="?", default="cleveland", help="market name (e.g. cleveland, detroit, youngstown) or 'all'")
    ap.add_argument("--budget", type=float, help="available cash budget (cash to close + rehab)")
    ap.add_argument("--stretch", type=float, help="stretch capital window beyond budget (default: 40 percent of budget or $25k)")
    ap.add_argument("--json", action="store_true", help="output structured JSON")
    args = ap.parse_args(argv)

    market = args.market
    if market.endswith(".json"):
        market = Path(market).stem

    recs = load_properties_for_market(market)
    if not recs:
        # Fall back to loading all markets if specific market has no index entries yet
        recs = load_properties_for_market("all")

    rec_analysis = run.recommend_deals(recs, budget=args.budget, stretch=args.stretch)

    if args.json:
        # Clean up unpicklable/cyclic keys before serializing
        clean_bib = dict(rec_analysis["best_in_budget"]) if rec_analysis["best_in_budget"] else None
        clean_bs = dict(rec_analysis["best_stretch"]) if rec_analysis["best_stretch"] else None
        if clean_bs and "deal" in clean_bs:
            clean_bs["deal"] = dict(clean_bs["deal"])

        out = {
            "market": market,
            "budget": rec_analysis["budget"],
            "stretch_ceiling": rec_analysis["stretch_ceiling"],
            "stretch_window": rec_analysis["stretch_window"],
            "best_in_budget": clean_bib,
            "best_stretch": clean_bs,
            "total_analyzed": len(recs),
            "in_budget_count": len(rec_analysis["in_budget"]),
            "stretch_count": len(rec_analysis["stretch_pool"]),
        }
        json.dump(out, sys.stdout, indent=2, default=str)
        sys.stdout.write("\n")
    else:
        print(render_recommendation_cli(rec_analysis, market))


if __name__ == "__main__":
    main()
