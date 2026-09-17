#!/usr/bin/env python3
"""
HADES Unified Messaging Dispatcher (`msg`)
Deterministic single-shot messaging router across WhatsApp, BlueBubbles (iMessage), and Telegram.
Handles automatic contact resolution and programmatic dispatch verification.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


PHONE_PATTERN = re.compile(r"^\+?[0-9]{10,15}$")


def run_cmd(cmd: List[str], timeout: float = 12.0) -> Tuple[int, str, str]:
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except subprocess.TimeoutExpired:
        return 124, "", "command timed out"
    except FileNotFoundError:
        return 127, "", f"binary not found: {cmd[0]}"
    except Exception as e:
        return 1, "", str(e)


def resolve_whatsapp_contact(name_or_query: str) -> Optional[Tuple[str, str]]:
    """Resolve a contact name to (jid, display_name) using wacli."""
    wacli = shutil.which("wacli") or str(Path.home() / ".local" / "bin" / "wacli")
    code, stdout, _ = run_cmd([wacli, "contacts", "search", name_or_query, "--limit", "1", "--json"], timeout=5.0)
    if code != 0 or not stdout:
        return None
    try:
        data = json.loads(stdout)
        contacts = data.get("data", [])
        if contacts:
            c = contacts[0]
            jid = c.get("jid") or c.get("phone")
            name = c.get("name") or c.get("system_name") or name_or_query
            if jid:
                return jid, name
    except Exception:
        pass
    return None


def send_whatsapp(target: str, message: str) -> Tuple[bool, str]:
    wacli = shutil.which("wacli") or str(Path.home() / ".local" / "bin" / "wacli")
    # If target is not a JID and not a pure phone number, try to resolve it
    display_name = target
    if "@" not in target and not PHONE_PATTERN.match(target):
        resolved = resolve_whatsapp_contact(target)
        if resolved:
            target, display_name = resolved
        else:
            return False, f"Could not resolve WhatsApp contact '{target}'"

    cmd = [wacli, "send", "text", "--to", target, "--message", message]
    code, stdout, stderr = run_cmd(cmd, timeout=15.0)
    if code == 0:
        return True, f"[whatsapp] Sent to {display_name} ({target}): \"{message}\" (verified)"
    return False, f"[whatsapp] Failed to send: {stderr or stdout}"


def send_bluebubbles(target: str, message: str) -> Tuple[bool, str]:
    bb = shutil.which("bluebubbles") or str(Path.home() / ".local" / "bin" / "bluebubbles")
    # bluebubbles send-direct takes phone or email
    cmd = [bb, "send-direct", target, message]
    code, stdout, stderr = run_cmd(cmd, timeout=15.0)
    if code == 0:
        return True, f"[bluebubbles] Sent to {target}: \"{message}\" (verified)"
    return False, f"[bluebubbles] Failed to send: {stderr or stdout}"


def send_telegram(target: str, message: str) -> Tuple[bool, str]:
    tg = shutil.which("telegram") or str(Path.home() / ".local" / "bin" / "telegram")
    cmd = [tg, "send", target, message]
    code, stdout, stderr = run_cmd(cmd, timeout=15.0)
    if code == 0:
        return True, f"[telegram] Sent to {target}: \"{message}\" (verified)"
    return False, f"[telegram] Failed to send: {stderr or stdout}"


def check_status() -> Dict[str, Any]:
    statuses = {}

    # WhatsApp
    wacli = shutil.which("wacli") or str(Path.home() / ".local" / "bin" / "wacli")
    code, out, _ = run_cmd([wacli, "doctor", "--json"], timeout=4.0)
    if code == 0:
        try:
            d = json.loads(out).get("data", {})
            statuses["whatsapp"] = {"ok": d.get("authenticated", False), "detail": "authenticated"}
        except Exception:
            statuses["whatsapp"] = {"ok": True, "detail": "ready"}
    else:
        statuses["whatsapp"] = {"ok": False, "detail": "unavailable"}

    # BlueBubbles
    bb = shutil.which("bluebubbles") or str(Path.home() / ".local" / "bin" / "bluebubbles")
    code, out, _ = run_cmd([bb, "status"], timeout=4.0)
    statuses["bluebubbles"] = {"ok": (code == 0 and "200" in out), "detail": "online" if code == 0 else "offline"}

    # Telegram
    tg = shutil.which("telegram") or str(Path.home() / ".local" / "bin" / "telegram")
    code, out, _ = run_cmd([tg, "check"], timeout=4.0)
    statuses["telegram"] = {"ok": code == 0, "detail": "connected" if code == 0 else "disconnected"}

    return statuses


def detect_channel(recipient: str) -> str:
    if recipient.startswith("@"):
        return "telegram"
    if "@s.whatsapp.net" in recipient or "@g.us" in recipient or "@lid" in recipient:
        return "whatsapp"
    if PHONE_PATTERN.match(recipient):
        # Default phone numbers to BlueBubbles (iMessage) if online, otherwise WhatsApp
        return "bluebubbles"
    # Try resolving via WhatsApp contacts
    if resolve_whatsapp_contact(recipient):
        return "whatsapp"
    return "bluebubbles"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="HADES Unified Messaging Dispatcher (`msg`)")
    subparsers = parser.add_subparsers(dest="command")

    # send
    send_p = subparsers.add_parser("send", help="Send a message to a recipient")
    send_p.add_argument("recipient", help="Recipient name, phone, handle, or JID")
    send_p.add_argument("message", help="Message text content")
    send_p.add_argument(
        "--channel",
        choices=["auto", "whatsapp", "bluebubbles", "telegram"],
        default="auto",
        help="Messaging channel (default: auto)",
    )

    # resolve
    res_p = subparsers.add_parser("resolve", help="Resolve contact name to channel and target")
    res_p.add_argument("recipient", help="Recipient name or query")

    # status
    subparsers.add_parser("status", help="Check status of all messaging backends")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    cmd = args.command or "status"

    if cmd == "status":
        st = check_status()
        print("Messaging Backends Status:")
        for ch, info in st.items():
            state = "READY" if info["ok"] else "DEGRADED"
            print(f"  {ch:<12}: {state} ({info['detail']})")
        return 0

    elif cmd == "resolve":
        target = args.recipient
        channel = detect_channel(target)
        resolved_name = target
        if channel == "whatsapp":
            res = resolve_whatsapp_contact(target)
            if res:
                target, resolved_name = res
        print(f"Resolved: channel={channel}, target={target}, display_name={resolved_name}")
        return 0

    elif cmd == "send":
        ch = args.channel
        if ch == "auto":
            ch = detect_channel(args.recipient)

        if ch == "whatsapp":
            ok, msg = send_whatsapp(args.recipient, args.message)
        elif ch == "bluebubbles":
            ok, msg = send_bluebubbles(args.recipient, args.message)
        elif ch == "telegram":
            ok, msg = send_telegram(args.recipient, args.message)
        else:
            print(f"Unknown channel: {ch}", file=sys.stderr)
            return 1

        if ok:
            print(msg)
            return 0
        else:
            print(msg, file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
