#!/usr/bin/env python3
"""Apify Local Skill CLI.

Deterministic CLI for Apify REST API, Actor execution, and People Search adapter.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure local package path resolution
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from adapters.people_search import search_people, execute_actor_sync


def resolve_token() -> str:
    """Resolve APIFY_TOKEN from environment, ~/.local/bin/env, or Bitwarden."""
    token = os.environ.get("APIFY_TOKEN")
    if token and token.startswith("apify_api_"):
        return token

    # Check ~/.local/bin/env
    env_path = Path.home() / ".local" / "bin" / "env"
    if env_path.exists():
        try:
            content = env_path.read_text()
            for line in content.splitlines():
                line = line.strip()
                if line.startswith("export APIFY_TOKEN="):
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if val.startswith("apify_api_"):
                        os.environ["APIFY_TOKEN"] = val
                        return val
        except Exception:
            pass

    # Fallback to Bitwarden
    try:
        raw_bw = subprocess.check_output(["bw", "get", "item", "Apify"], stderr=subprocess.DEVNULL).decode()
        data = json.loads(raw_bw)
        for field in data.get("fields", []):
            if field.get("name") == "token" and field.get("value", "").startswith("apify_api_"):
                val = field["value"]
                os.environ["APIFY_TOKEN"] = val
                return val
    except Exception:
        pass

    print("Error: APIFY_TOKEN not found in environment, ~/.local/bin/env, or Bitwarden.", file=sys.stderr)
    print("Run `apify status` or set APIFY_TOKEN in ~/.local/bin/env.", file=sys.stderr)
    sys.exit(1)


def cmd_status(args: argparse.Namespace) -> None:
    """Check Apify account status, plan, usage, and token validity."""
    token = resolve_token()
    url = "https://api.apify.com/v2/users/me"

    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "User-Agent": "HADES-Apify/1.0",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8")).get("data", {})
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"Error {e.code}: {body}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Failed to connect to Apify API: {e}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(data, indent=2))
        return

    username = data.get("username", "Unknown")
    email = data.get("email", "Unknown")
    user_id = data.get("id", "Unknown")
    plan = data.get("plan", {})
    plan_name = plan.get("name", "Free / Community")
    monthly_budget = plan.get("monthlyUsageUsd", 5.0)
    current_billing = data.get("currentBillingPeriod", {})
    current_usage = current_billing.get("usageUsd", 0.0)

    print("Apify Account Status:")
    print(f"  User:     {username} ({user_id})")
    print(f"  Email:    {email}")
    print(f"  Plan:     {plan_name}")
    print(f"  Usage:    ${current_usage:.2f} / ${monthly_budget:.2f}")
    print(f"  Token:    {token[:10]}...{token[-4:]} (Active)")


def cmd_run(args: argparse.Namespace) -> None:
    """Run an actor synchronously and output dataset items."""
    token = resolve_token()
    actor_id = args.actor_id

    # Parse payload
    payload: Dict[str, Any] = {}
    if args.input:
        if args.input.startswith("@"):
            filepath = Path(args.input[1:]).expanduser()
            if not filepath.exists():
                print(f"Error: input file {filepath} not found", file=sys.stderr)
                sys.exit(1)
            payload = json.loads(filepath.read_text())
        else:
            payload = json.loads(args.input)

    try:
        items = execute_actor_sync(actor_id, payload, token, timeout_secs=args.timeout)
    except Exception as e:
        print(f"Actor run failed: {e}", file=sys.stderr)
        sys.exit(1)

    output_str = json.dumps(items, indent=2)
    if args.output:
        out_path = Path(args.output).expanduser()
        out_path.write_text(output_str)
        print(f"Results ({len(items)} items) written to {out_path}")
    else:
        print(output_str)


def cmd_people_search(args: argparse.Namespace) -> None:
    """Run reverse people, phone, or address search."""
    token = resolve_token()

    if not (args.phone or args.name or args.address):
        print("Error: Specify at least one of --phone, --name, or --address", file=sys.stderr)
        sys.exit(1)

    try:
        results = search_people(
            token=token,
            phone=args.phone,
            name=args.name,
            city=args.city,
            state=args.state,
            address=args.address,
            max_items=args.max_items,
            timeout_secs=args.timeout,
        )
    except Exception as e:
        print(f"Search failed: {e}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(results, indent=2))
        return

    if not results:
        print("No matching records found.")
        return

    print(f"Found {len(results)} candidate(s):\n")
    for i, p in enumerate(results, start=1):
        print(f"[{i}] {p.get('full_name')} (Age: {p.get('age') or 'N/A'})")
        if p.get("current_address"):
            print(f"    Current Address: {p.get('current_address')}")
        if p.get("past_addresses"):
            print(f"    Past Addresses:  {', '.join(p.get('past_addresses')[:3])}")
        if p.get("phones"):
            print(f"    Phones:")
            for ph in p.get("phones", []):
                print(f"      • {ph}")
        if p.get("emails"):
            print(f"    Emails:")
            for em in p.get("emails", []):
                print(f"      • {em}")
        if p.get("relatives"):
            print(f"    Relatives:       {', '.join(p.get('relatives')[:5])}")
        if p.get("associates"):
            print(f"    Associates:      {', '.join(p.get('associates')[:5])}")
        if p.get("profile_url"):
            print(f"    Source URL:      {p.get('profile_url')}")
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description="HADES Apify CLI Skill")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # status
    p_status = subparsers.add_parser("status", help="Check Apify account status and token validity")
    p_status.add_argument("--json", action="store_true", help="Output raw JSON")
    p_status.set_defaults(func=cmd_status)

    # run
    p_run = subparsers.add_parser("run", help="Run an Apify actor synchronously")
    p_run.add_argument("actor_id", help="Actor identifier (e.g. username/actor-name or actorId)")
    p_run.add_argument("--input", "-i", help="JSON input string or @filepath")
    p_run.add_argument("--timeout", "-t", type=int, default=180, help="Timeout in seconds (default: 180)")
    p_run.add_argument("--output", "-o", help="File to write output JSON")
    p_run.set_defaults(func=cmd_run)

    # people-search
    p_ps = subparsers.add_parser("people-search", help="Perform reverse phone/name/address search")
    p_ps.add_argument("--phone", "-p", help="Phone number to reverse lookup")
    p_ps.add_argument("--name", "-n", help="Full name to lookup")
    p_ps.add_argument("--city", "-c", help="City filter")
    p_ps.add_argument("--state", "-s", help="2-letter state filter (e.g. TX, NY)")
    p_ps.add_argument("--address", "-a", help="Street address to reverse lookup")
    p_ps.add_argument("--max-items", "-m", type=int, default=3, help="Max candidates to retrieve (default: 3)")
    p_ps.add_argument("--timeout", "-t", type=int, default=180, help="Actor timeout in seconds (default: 180)")
    p_ps.add_argument("--json", action="store_true", help="Output raw normalized JSON")
    p_ps.set_defaults(func=cmd_people_search)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
