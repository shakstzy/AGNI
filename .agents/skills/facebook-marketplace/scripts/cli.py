#!/usr/bin/env python3
"""
HADES Facebook Marketplace CLI (fbm)
Calls the facebook-marketplace MCP server via mcporter to provide a deterministic,
token-efficient CLI with zero context bloat.
"""

from __future__ import annotations
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

METRO_PRESETS: Dict[str, Dict[str, Any]] = {
    "austin": {"name": "Austin, TX", "lat": 30.2672, "lng": -97.7431, "radius": 30},
    "sf": {"name": "San Francisco, CA", "lat": 37.7749, "lng": -122.4194, "radius": 35},
    "nyc": {"name": "New York, NY", "lat": 40.7128, "lng": -74.0060, "radius": 25},
    "la": {"name": "Los Angeles, CA", "lat": 34.0522, "lng": -118.2437, "radius": 35},
    "miami": {"name": "Miami, FL", "lat": 25.7617, "lng": -80.1918, "radius": 30},
    "dallas": {"name": "Dallas, TX", "lat": 32.7767, "lng": -96.7970, "radius": 35},
    "seattle": {"name": "Seattle, WA", "lat": 47.6062, "lng": -122.3321, "radius": 30},
    "chicago": {"name": "Chicago, IL", "lat": 41.8781, "lng": -87.6298, "radius": 30},
}

SESSION_DIR = Path.home() / ".fb-marketplace"
SESSION_FILE = SESSION_DIR / "cookies.json"
HADES_BROWSER_PROFILE = Path("/home/shakstzy/HADES/.agents/skills/browser/sitemaps/facebook.com/profiles/adithya")


def call_mcporter(tool: str, args: List[str]) -> subprocess.CompletedProcess:
    cmd = ["mcporter", "call", f"facebook-marketplace.{tool}"] + args
    return subprocess.run(cmd, capture_output=True, text=True)


def extract_json_or_text(output: str) -> Any:
    trimmed = output.strip()
    # Check if the output contains a JSON object or array
    match = re.search(r'(\[.*\]|\{.*\})', trimmed, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass
    return trimmed


def cmd_status(args: argparse.Namespace) -> None:
    # 1. Check cookies existence
    has_session_file = SESSION_FILE.exists()
    has_env = bool(os.environ.get("FB_COOKIES") or os.environ.get("FB_COOKIE_STRING"))
    browser_user_data = HADES_BROWSER_PROFILE / "user_data"
    has_browser_profile = browser_user_data.exists()

    # 2. Check MCPorter server registration
    mcp_check = subprocess.run(["mcporter", "list", "facebook-marketplace"], capture_output=True, text=True)
    mcp_registered = mcp_check.returncode == 0

    # 3. Check monitors
    monitors_res = call_mcporter("list_monitors", [])
    monitors_raw = monitors_res.stdout.strip()

    status_data = {
        "mcp_server": "facebook-marketplace",
        "mcp_status": "ONLINE" if mcp_registered else "NOT_REGISTERED",
        "auth_methods": {
            "session_file": str(SESSION_FILE) if has_session_file else None,
            "env_cookies": has_env,
            "browser_profile": str(HADES_BROWSER_PROFILE) if has_browser_profile else None,
        },
        "monitors": monitors_raw if monitors_res.returncode == 0 else "Unavailable",
        "supported_metros": list(METRO_PRESETS.keys()),
    }

    if args.json:
        print(json.dumps(status_data, indent=2))
        return

    print("════════════════════════════════════════════════════════════════")
    print(" HADES FACEBOOK MARKETPLACE CLI (fbm)")
    print("────────────────────────────────────────────────────────────────")
    print(f" MCP Server Status:   {status_data['mcp_status']}")
    print(f" Session Cookie File: {'FOUND (' + str(SESSION_FILE) + ')' if has_session_file else 'NOT FOUND'}")
    print(f" Environment Cookie:  {'SET' if has_env else 'NOT SET'}")
    print(f" Browser Profile:     {'PRESENT' if has_browser_profile else 'MISSING'}")
    print(f" Active Monitors:     {status_data['monitors']}")
    print(f" Available Metros:    {', '.join(METRO_PRESETS.keys())}")
    print("════════════════════════════════════════════════════════════════")


def cmd_auth(args: argparse.Namespace) -> None:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)

    if args.cookie:
        # Save raw cookie string or JSON
        raw = args.cookie.strip()
        SESSION_FILE.write_text(raw)
        print(f"Successfully saved session cookies to {SESSION_FILE}")
        return

    if args.file:
        p = Path(args.file)
        if not p.is_file():
            print(f"Error: File not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        SESSION_FILE.write_text(p.read_text())
        print(f"Successfully imported cookies from {args.file} to {SESSION_FILE}")
        return

    # Check status
    if SESSION_FILE.exists():
        print(f"Active session file present at {SESSION_FILE} ({SESSION_FILE.stat().st_size} bytes)")
    else:
        print("No session file found at ~/.fb-marketplace/cookies.json")
        print("\nTo authenticate Facebook:")
        print("1. Pass raw cookie string: fbm auth --cookie 'c_user=...; xs=...;'")
        print("2. Or pass a exported cookie JSON file: fbm auth --file /path/to/cookies.json")
        print("3. Or log into Facebook in the profile: browser opencli --site facebook.com --profile adithya")


def cmd_search(args: argparse.Namespace) -> None:
    lat = args.lat
    lng = args.lng
    radius = args.radius or 50

    if args.market:
        preset = METRO_PRESETS.get(args.market.lower())
        if not preset:
            print(f"Unknown market '{args.market}'. Available: {list(METRO_PRESETS.keys())}", file=sys.stderr)
            sys.exit(1)
        lat = preset["lat"]
        lng = preset["lng"]
        radius = args.radius or preset["radius"]

    if lat is None or lng is None:
        # Default to Austin
        lat = 30.2672
        lng = -97.7431

    call_args = [
        f"query:{args.query}",
        f"latitude:{lat}",
        f"longitude:{lng}",
        f"radius_km:{radius}",
        f"limit:{args.limit or 20}",
    ]
    if args.min_price is not None:
        call_args.append(f"min_price:{args.min_price}")
    if args.max_price is not None:
        call_args.append(f"max_price:{args.max_price}")

    res = call_mcporter("search_listings", call_args)
    if res.returncode != 0:
        err = res.stderr.strip() or res.stdout.strip()
        print(f"Search failed: {err}", file=sys.stderr)
        sys.exit(res.returncode)

    parsed = extract_json_or_text(res.stdout)

    if args.json:
        if isinstance(parsed, (dict, list)):
            print(json.dumps(parsed, indent=2))
        else:
            print(parsed)
        return

    # Concise token-efficient table formatting
    if isinstance(parsed, list):
        items = parsed
    elif isinstance(parsed, dict) and "listings" in parsed:
        items = parsed["listings"]
    else:
        print(res.stdout.strip())
        return

    if not items:
        print(f"No listings found for '{args.query}' (Radius: {radius}km).")
        return

    print(f"\nDiscovered {len(items)} listings for '{args.query}':")
    print(f"{'ID':<18} {'PRICE':<10} {'TITLE':<45} {'LOCATION':<20} {'URL'}")
    print("─" * 115)
    for it in items[: args.limit or 20]:
        lid = str(it.get("id") or it.get("listing_id") or "")[:17]
        price = str(it.get("price") or it.get("formatted_price") or "$0")[:9]
        title = str(it.get("title") or it.get("name") or "")[:43]
        loc = str(it.get("location") or it.get("city") or "")[:18]
        url = it.get("url") or f"https://www.facebook.com/marketplace/item/{lid}/"
        print(f"{lid:<18} {price:<10} {title:<45} {loc:<20} {url}")


def cmd_free(args: argparse.Namespace) -> None:
    args.min_price = 0
    args.max_price = 0
    if not args.query:
        args.query = "free"
    cmd_search(args)


def cmd_listing(args: argparse.Namespace) -> None:
    res = call_mcporter("get_listing", [f"listing_id:{args.listing_id}"])
    if res.returncode != 0:
        err = res.stderr.strip() or res.stdout.strip()
        print(f"Failed to fetch listing {args.listing_id}: {err}", file=sys.stderr)
        sys.exit(res.returncode)

    parsed = extract_json_or_text(res.stdout)
    if args.json:
        if isinstance(parsed, (dict, list)):
            print(json.dumps(parsed, indent=2))
        else:
            print(parsed)
        return

    if isinstance(parsed, dict):
        print("════════════════════════════════════════════════════════════════")
        print(f" LISTING: {parsed.get('title') or args.listing_id}")
        print("────────────────────────────────────────────────────────────────")
        print(f" Price:       {parsed.get('price') or '$0'}")
        print(f" Location:    {parsed.get('location') or 'N/A'}")
        print(f" Category:    {parsed.get('category') or 'N/A'}")
        print(f" Seller:      {parsed.get('seller_name') or 'N/A'}")
        print(f" URL:         https://www.facebook.com/marketplace/item/{args.listing_id}/")
        print("────────────────────────────────────────────────────────────────")
        print(" DESCRIPTION:")
        desc = (parsed.get("description") or "No description provided.").strip()
        print(desc[:500] + ("..." if len(desc) > 500 else ""))
        if parsed.get("photos"):
            print("────────────────────────────────────────────────────────────────")
            print(f" Photos ({len(parsed['photos'])}):")
            for p in parsed["photos"][:3]:
                print(f"  - {p}")
        print("════════════════════════════════════════════════════════════════")
    else:
        print(res.stdout.strip())


def cmd_location(args: argparse.Namespace) -> None:
    res = call_mcporter("search_location", [f"query:{args.query}"])
    if res.returncode != 0:
        err = res.stderr.strip() or res.stdout.strip()
        print(f"Failed to search location: {err}", file=sys.stderr)
        sys.exit(res.returncode)

    parsed = extract_json_or_text(res.stdout)
    if args.json:
        if isinstance(parsed, (dict, list)):
            print(json.dumps(parsed, indent=2))
        else:
            print(parsed)
        return

    print(res.stdout.strip())


def cmd_monitor(args: argparse.Namespace) -> None:
    action = args.action
    if action == "list":
        res = call_mcporter("list_monitors", [])
        print(res.stdout.strip())
    elif action == "check":
        sub_args = []
        if args.name:
            sub_args.append(f"monitor_name:{args.name}")
        res = call_mcporter("check_monitors", sub_args)
        print(res.stdout.strip())
    elif action == "delete":
        if not args.name:
            print("Error: --name is required to delete a monitor", file=sys.stderr)
            sys.exit(1)
        res = call_mcporter("delete_monitor", [f"name:{args.name}"])
        print(res.stdout.strip())
    elif action == "add":
        if not args.name or not args.query:
            print("Error: --name and --query are required to add a monitor", file=sys.stderr)
            sys.exit(1)
        lat = args.lat or 30.2672
        lng = args.lng or -97.7431
        sub_args = [
            f"name:{args.name}",
            f"query:{args.query}",
            f"latitude:{lat}",
            f"longitude:{lng}",
            f"radius_km:{args.radius or 30}",
        ]
        if args.min_price is not None:
            sub_args.append(f"min_price:{args.min_price}")
        if args.max_price is not None:
            sub_args.append(f"max_price:{args.max_price}")
        res = call_mcporter("monitor_search", sub_args)
        print(res.stdout.strip())


def main() -> None:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", help="Emit raw JSON")

    parser = argparse.ArgumentParser(description="HADES Facebook Marketplace CLI (fbm)", parents=[common])
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # status
    p_stat = subparsers.add_parser("status", parents=[common], help="Inspect session, server, and monitors")
    p_stat.set_defaults(func=cmd_status)

    # auth
    p_auth = subparsers.add_parser("auth", parents=[common], help="Manage or import Facebook session cookies")
    p_auth.add_argument("--cookie", type=str, help="Raw cookie string or JSON string")
    p_auth.add_argument("--file", type=str, help="Path to exported cookie JSON file")
    p_auth.set_defaults(func=cmd_auth)

    # search
    p_srch = subparsers.add_parser("search", parents=[common], help="Search Marketplace listings")
    p_srch.add_argument("query", type=str, help="Search query")
    p_srch.add_argument("--market", type=str, choices=list(METRO_PRESETS.keys()), help="Target metro preset")
    p_srch.add_argument("--lat", type=float, help="Latitude")
    p_srch.add_argument("--lng", type=float, help="Longitude")
    p_srch.add_argument("--radius", type=int, help="Radius in km")
    p_srch.add_argument("--min-price", type=int, help="Min price ($)")
    p_srch.add_argument("--max-price", type=int, help="Max price ($)")
    p_srch.add_argument("--limit", type=int, default=20, help="Max results")
    p_srch.set_defaults(func=cmd_search)

    # free
    p_free = subparsers.add_parser("free", parents=[common], help="Search $0 freebie listings")
    p_free.add_argument("--query", type=str, default="free", help="Search query or keyword")
    p_free.add_argument("--market", type=str, default="austin", choices=list(METRO_PRESETS.keys()), help="Metro preset")
    p_free.add_argument("--lat", type=float, help="Latitude")
    p_free.add_argument("--lng", type=float, help="Longitude")
    p_free.add_argument("--radius", type=int, help="Radius in km")
    p_free.add_argument("--limit", type=int, default=20, help="Max results")
    p_free.set_defaults(func=cmd_free)

    # listing
    p_list = subparsers.add_parser("listing", parents=[common], help="Get listing details by ID")
    p_list.add_argument("listing_id", type=str, help="Marketplace listing ID")
    p_list.set_defaults(func=cmd_listing)

    # location
    p_loc = subparsers.add_parser("location", parents=[common], help="Resolve location coordinates")
    p_loc.add_argument("query", type=str, help="City or address query")
    p_loc.set_defaults(func=cmd_location)

    # monitor
    p_mon = subparsers.add_parser("monitor", parents=[common], help="Manage search monitors")
    p_mon.add_argument("action", choices=["list", "check", "add", "delete"], help="Monitor action")
    p_mon.add_argument("--name", type=str, help="Monitor name")
    p_mon.add_argument("--query", type=str, help="Monitor query (for add)")
    p_mon.add_argument("--lat", type=float, help="Latitude")
    p_mon.add_argument("--lng", type=float, help="Longitude")
    p_mon.add_argument("--radius", type=int, default=30, help="Radius in km")
    p_mon.add_argument("--min-price", type=int, help="Min price")
    p_mon.add_argument("--max-price", type=int, help="Max price")
    p_mon.set_defaults(func=cmd_monitor)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
