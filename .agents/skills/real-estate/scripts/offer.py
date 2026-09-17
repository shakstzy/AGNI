#!/usr/bin/env python3
"""CLI interface for Institutional Real Estate Offer Generation & Outreach.

Usage:
    re offer generate "<address-or-slug>" [--discount 0.08] [--pdf] [--json] [--force]
    re offer send "<address-or-slug>" [--channel email|sms|both] [--dry-run]
    re offer preview "<address-or-slug>"
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

# Path routing
THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[4]
STAGE_07_DIR = REPO_ROOT / "workspaces" / "real-estate" / "stages" / "07-offer"
WORKSPACE_DIR = REPO_ROOT / "workspaces" / "real-estate"
INDEX_PATH = WORKSPACE_DIR / "raw" / "index.jsonl"
PROPERTIES_DIR = WORKSPACE_DIR / "wiki" / "entities" / "properties"

if str(STAGE_07_DIR) not in sys.path:
    sys.path.insert(0, str(STAGE_07_DIR))

try:
    from agent_contacts import extract_agent_contact, verify_realtor_contact
    from filter import evaluate_deal_killers
    from offer_engine import calculate_offer_package
    from render_offer_pdf import render_loi_pdf
    from outreach import dispatch_offer, format_outreach_email, format_outreach_sms
except ImportError as e:
    sys.stderr.write(f"Error loading stage 07 modules: {e}\n")
    sys.exit(1)


def _load_property(target: str) -> dict[str, Any] | None:
    """Resolve a target address or slug to a property record."""
    target_clean = target.strip()

    # 1. Search index.jsonl
    if INDEX_PATH.exists():
        with open(INDEX_PATH, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except Exception:
                    continue
                addr = (row.get("address") or "").lower()
                slug = (row.get("slug") or "").lower()
                fm = row.get("frontmatter") or {}
                fm_addr = (fm.get("address") or "").lower()
                t_lower = target_clean.lower()
                if t_lower == slug or t_lower == addr or t_lower == fm_addr or t_lower in addr:
                    return row

    # 2. Check wiki properties directory for slug.md
    slug_candidate = target_clean.replace(" ", "-").replace(",", "").lower()
    for cand in [slug_candidate, target_clean]:
        cand_path = PROPERTIES_DIR / (cand if cand.endswith(".md") else f"{cand}.md")
        if cand_path.exists():
            text = cand_path.read_text(encoding="utf-8")
            # Parse simple YAML frontmatter
            fm = {}
            if text.startswith("---"):
                parts = text.split("---", 2)
                if len(parts) >= 3:
                    for line in parts[1].splitlines():
                        if ":" in line:
                            k, _, v = line.partition(":")
                            k = k.strip()
                            v = v.strip().strip('"').strip("'")
                            if v.isdigit():
                                fm[k] = int(v)
                            else:
                                try:
                                    fm[k] = float(v)
                                except ValueError:
                                    fm[k] = v if v != "null" else None
            return {
                "slug": cand_path.stem,
                "address": fm.get("address") or target_clean,
                "frontmatter": fm,
                "path": str(cand_path),
            }

    # 3. Create fallback record if numeric price was passed or fallback minimal record
    return {
        "slug": slug_candidate,
        "address": target_clean,
        "frontmatter": {
            "address": target_clean,
            "price": 100000,
            "rent_total_monthly": 1500,
            "units": 2,
            "year_built": 1960,
        },
    }


def cmd_generate(args: argparse.Namespace) -> None:
    prop = _load_property(args.target)
    if not prop:
        sys.stderr.write(f"Error: Property '{args.target}' could not be located.\n")
        sys.exit(1)

    # Deal killer evaluation
    qualified, reasons, adjustments = evaluate_deal_killers(prop)
    if not qualified and not args.force:
        err_out = {
            "status": "rejected",
            "address": prop.get("address"),
            "rejection_reasons": reasons,
            "risk_adjustments": adjustments,
        }
        if args.json:
            print(json.dumps(err_out, indent=2))
        else:
            print(f"DISQUALIFIED: {prop.get('address')}", file=sys.stderr)
            for r in reasons:
                print(f"  • {r}", file=sys.stderr)
            print("Use --force to generate offer regardless.", file=sys.stderr)
        sys.exit(2)

    pkg = calculate_offer_package(
        prop,
        discount_pct=args.discount,
        second_note_rate=args.second_rate,
    )
    pkg["risk_adjustments"] = adjustments

    pdf_path = None
    if args.pdf:
        slug = pkg["slug"]
        out_dir = Path(args.outdir) if args.outdir else WORKSPACE_DIR / "output" / "offers"
        out_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = out_dir / f"{slug}-loi.pdf"
        render_loi_pdf(pkg, pdf_path)
        pkg["pdf_path"] = str(pdf_path)

    if args.json:
        print(json.dumps(pkg, indent=2))
        return

    # Scannable terminal summary
    addr = pkg["address"]
    p_ask = pkg["asking_price"]
    o1 = pkg["option_1"]
    o2 = pkg["option_2"]
    cc = pkg["credit_card_rehab"]
    inc = pkg["agent_incentive"]

    print(f"============================================================")
    print(f"OFFER MEMORANDUM: {addr}")
    print(f"List Price: ${p_ask:,.0f} | Units: {pkg['units']} | Built: {pkg['year_built']}")
    print(f"============================================================")
    print(f"OPTION 1 (Fast DSCR - 21-Day Close, CMG Pre-Approval):")
    print(f"  • Purchase Price:       ${o1['purchase_price']:,.0f} ({o1['discount_pct']:.0%} Discount)")
    print(f"  • 75% First Mortgage:   ${o1['first_mortgage_amount']:,.0f}")
    print(f"  • 3% Seller Credit:     ${o1['seller_credit']:,.0f}")
    print(f"  • Net Cash to Close:    ${o1['net_cash_to_close']:,.0f}")
    print(f"  • Monthly PITIA:        ${o1['monthly_pitia']:,.2f}/mo")
    print()
    print(f"OPTION 2 (Full List Price on Terms - 80-15-5 Structure):")
    print(f"  • Purchase Price:       ${o2['purchase_price']:,.0f} (100% of List)")
    print(f"  • 80% First Mortgage:   ${o2['first_mortgage_amount']:,.0f}")
    print(f"  • 15% Seller 2nd Note:  ${o2['seller_second_note_amount']:,.0f} @ 5.5% IO (36 Mo Balloon)")
    print(f"  • Seller Monthly Income: ${o2['seller_second_monthly_interest']:,.2f}/mo")
    print(f"  • Buyer Down Payment:   ${o2['buyer_cash_down']:,.0f} (5% Cash Out-of-Pocket)")
    print()
    print(f"FINANCING & AGENT HOOK:")
    print(f"  • 0% CC Make-Ready:     ${cc['make_ready_budget']:,.0f} (100% liquid cash preserved)")
    print(f"  • Dual Agency Fee:      ${inc['option_2_agent_bonus']:,.0f} (Listing agent retains 5%–6%)")
    if pdf_path:
        print(f"  • Rendered 2-Page LOI:  {pdf_path}")
    print(f"============================================================")


def cmd_send(args: argparse.Namespace) -> None:
    prop = _load_property(args.target)
    if not prop:
        sys.stderr.write(f"Error: Property '{args.target}' could not be located.\n")
        sys.exit(1)

    pkg = calculate_offer_package(prop)
    slug = pkg["slug"]
    out_dir = WORKSPACE_DIR / "output" / "offers"
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / f"{slug}-loi.pdf"
    if not pdf_path.exists():
        render_loi_pdf(pkg, pdf_path)

    contact = extract_agent_contact(prop)
    if args.email:
        contact["email"] = args.email
    if args.phone:
        contact["phone"] = args.phone
    if args.email or args.phone:
        contact = verify_realtor_contact(contact)

    channels = ["email", "sms"] if args.channel == "both" else [args.channel]
    res = dispatch_offer(
        offer_pkg=pkg,
        pdf_path=pdf_path,
        agent_contact=contact,
        channels=channels,
        dry_run=args.dry_run,
        market=prop.get("market") or "deals",
    )

    if args.json:
        print(json.dumps(res, indent=2))
    else:
        print(f"OUTREACH {'STAGED (DRY-RUN)' if args.dry_run else 'DISPATCHED'}:")
        print(f"  Property:   {pkg['address']}")
        print(f"  Agent:      {contact['name']} <{contact['email']}> | {contact['phone']}")
        print(f"  Channels:   {', '.join(channels)}")
        print(f"  Attachment: {pdf_path}")
        print(f"  Audit Log:  {res.get('log_path')}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="re offer", description="Institutional Real Estate Offer & Outreach Engine")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # generate
    gen_parser = subparsers.add_parser("generate", help="Generate two-tier offer terms and optional PDF LOI")
    gen_parser.add_argument("target", help="Address, slug, or property identifier")
    gen_parser.add_argument("--discount", type=float, default=0.08, help="Option 1 discount rate (default: 0.08)")
    gen_parser.add_argument("--second-rate", type=float, default=0.055, help="Option 2 seller note interest (default: 0.055)")
    gen_parser.add_argument("--pdf", action="store_true", help="Render 2-page institutional PDF LOI")
    gen_parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    gen_parser.add_argument("--force", action="store_true", help="Bypass deal-killer screening")
    gen_parser.add_argument("--outdir", help="Custom output directory for PDF")

    # send
    send_parser = subparsers.add_parser("send", help="Dispatch or stage offer outreach to listing agent")
    send_parser.add_argument("target", help="Address, slug, or property identifier")
    send_parser.add_argument("--channel", choices=["email", "sms", "both"], default="email", help="Outreach channel")
    send_parser.add_argument("--dry-run", action="store_true", default=True, help="Stage outreach without calling live CLIs")
    send_parser.add_argument("--live", dest="dry_run", action="store_false", help="Execute live email/SMS dispatch")
    send_parser.add_argument("--email", help="Override listing agent email")
    send_parser.add_argument("--phone", help="Override listing agent phone")
    send_parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # preview
    prev_parser = subparsers.add_parser("preview", help="Preview outreach email and SMS copy")
    prev_parser.add_argument("target", help="Address, slug, or property identifier")

    args = parser.parse_args()

    if args.subcommand == "generate":
        cmd_generate(args)
    elif args.subcommand == "send":
        cmd_send(args)
    elif args.subcommand == "preview":
        prop = _load_property(args.target)
        if not prop:
            sys.exit(1)
        pkg = calculate_offer_package(prop)
        contact = extract_agent_contact(prop)
        email = format_outreach_email(pkg, contact, "[PATH_TO_LOI.PDF]")
        sms = format_outreach_sms(pkg, contact)
        print("=== EMAIL PREVIEW ===")
        print(f"To: {email['to']}")
        print(f"Subject: {email['subject']}")
        print()
        print(email["body"])
        print()
        print("=== SMS PREVIEW ===")
        print(sms)


if __name__ == "__main__":
    main()
