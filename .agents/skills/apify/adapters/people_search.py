"""TruePeopleSearch & Skip Trace Adapter for Apify Local Skill.

Performs reverse people, phone, and address searches using Apify actors.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

PRIMARY_ACTOR = "jungle_synthesizer/truepeoplesearch-people-search-scraper"
FALLBACK_ACTOR = "apivault_labs/skip-trace-people-finder"
APIFY_API_BASE = "https://api.apify.com/v2"


def clean_phone(phone: str) -> str:
    """Strip formatting characters from phone string."""
    digits = re.sub(r"[^\d]", "", phone)
    if len(digits) == 11 and digits.startswith("1"):
        return digits[1:]
    return digits


def extract_e164(text: str) -> List[str]:
    """Extract standard 10-digit phone numbers formatted into (XXX) XXX-XXXX."""
    matches = re.findall(r"(?:\+?1[-.\s]?)?\(?([2-9][0-9]{2})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})", text)
    return [f"({m[0]}) {m[1]}-{m[2]}" for m in matches]


def normalize_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize raw actor result item into unified person structure."""
    phones_raw = item.get("phones") or []
    if isinstance(phones_raw, str):
        phones_raw = [phones_raw]

    emails_raw = item.get("emails") or []
    if isinstance(emails_raw, str):
        emails_raw = [emails_raw]

    # Handle TruePeopleSearch format
    full_name = item.get("fullName") or item.get("name") or ""
    age = item.get("age") or None
    current_address = item.get("currentAddress") or item.get("address") or None
    past_addresses = item.get("pastAddresses") or item.get("previousAddresses") or []
    relatives = item.get("relatives") or []
    associates = item.get("associates") or item.get("aliases") or []
    profile_url = item.get("profileUrl") or item.get("sourceUrl") or item.get("url") or None
    source = item.get("source") or "apify-people"

    return {
        "full_name": full_name,
        "age": age,
        "phones": phones_raw,
        "emails": emails_raw,
        "current_address": current_address,
        "past_addresses": past_addresses,
        "relatives": relatives,
        "associates": associates,
        "profile_url": profile_url,
        "source": source,
    }


def execute_actor_sync(
    actor_id: str,
    payload: Dict[str, Any],
    token: str,
    timeout_secs: int = 180,
) -> List[Dict[str, Any]]:
    """Execute Apify actor synchronously and fetch dataset items."""
    encoded_id = actor_id.replace("/", "~")
    url = f"{APIFY_API_BASE}/acts/{urllib.parse.quote(encoded_id)}/run-sync-get-dataset-items?timeout={timeout_secs}"

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "HADES-Apify/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout_secs + 15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, list):
                return data
            return []
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        try:
            err_json = json.loads(err_body)
            msg = err_json.get("error", {}).get("message") or err_body
        except Exception:
            msg = err_body
        raise RuntimeError(f"Apify actor error ({e.code}): {msg}")
    except Exception as e:
        raise RuntimeError(f"Request failed: {e}")


def search_people(
    token: str,
    phone: Optional[str] = None,
    name: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    address: Optional[str] = None,
    max_items: int = 5,
    timeout_secs: int = 180,
) -> List[Dict[str, Any]]:
    """Perform people lookup with TruePeopleSearch actor, normalizing results."""
    payload: Dict[str, Any] = {"maxItems": max_items}

    if phone:
        digits = clean_phone(phone)
        payload["searchMode"] = "phone"
        payload["phone"] = digits
    elif address:
        payload["searchMode"] = "address"
        payload["address"] = address
        if city:
            payload["city"] = city
        if state:
            payload["state"] = state
    elif name:
        payload["searchMode"] = "name"
        parts = name.strip().split(None, 1)
        payload["firstName"] = parts[0]
        if len(parts) > 1:
            payload["lastName"] = parts[1]
        if city:
            payload["city"] = city
        if state:
            payload["state"] = state
    else:
        raise ValueError("Must provide at least one search parameter: --phone, --name, or --address")

    # Run primary actor
    try:
        raw_items = execute_actor_sync(PRIMARY_ACTOR, payload, token, timeout_secs=timeout_secs)
    except Exception as primary_err:
        # Fallback to secondary actor if phone or name
        try:
            fb_payload: Dict[str, Any] = {"max_results": max_items}
            if phone:
                fb_payload["phone_number"] = [clean_phone(phone)]
            elif name:
                q = " ".join(filter(None, [name, city, state]))
                fb_payload["name"] = [q]
            raw_items = execute_actor_sync(FALLBACK_ACTOR, fb_payload, token, timeout_secs=timeout_secs)
        except Exception:
            raise primary_err

    # Normalize items
    results = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        # Skip disclaimer or notice objects
        if item.get("recordType") == "notice":
            continue
        results.append(normalize_item(item))

    return results
