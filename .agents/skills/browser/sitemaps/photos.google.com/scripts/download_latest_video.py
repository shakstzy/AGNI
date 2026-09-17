#!/usr/bin/env python3
"""Automated video downloader from Google Photos via Browser CDP."""

import json
import os
import sys
import time
import urllib.request
from pathlib import Path

CDP_PORT = 9226
CDP_BASE = f"http://127.0.0.1:{CDP_PORT}"

def check_auth_state() -> tuple[bool, str]:
    try:
        tabs = json.loads(urllib.request.urlopen(f"{CDP_BASE}/json/list", timeout=2.0).read())
    except Exception as e:
        return False, f"Cannot connect to Chrome on port {CDP_PORT}: {e}"

    pages = [t for t in tabs if t.get("type") == "page"]
    if not pages:
        return False, "No active browser tabs found."

    current_url = pages[0].get("url", "")
    if "accounts.google.com" in current_url:
        return False, f"Waiting on Google Sign-In at: {current_url}"
    if "photos.google.com/about" in current_url or "photos.google.com/login" in current_url:
        return False, f"Not authenticated yet (current URL: {current_url})"

    return True, f"Authenticated! Current URL: {current_url}"

def main():
    print(f"[*] Checking Google Photos browser session on CDP port {CDP_PORT}...")
    is_authed, status_msg = check_auth_state()
    print(f"[*] Status: {status_msg}")

    if not is_authed:
        print("\n[!] Action required: Please complete your Google Sign-in in the open browser window.")
        print("[!] Once signed in, run this script again or reply in the chat to proceed.")
        sys.exit(2)

    # Call browser-harness to navigate to videos and download
    cmd = f"""BU_CDP_URL="{CDP_BASE}" browser-harness <<'PY'
goto_url("https://photos.google.com/search/_m8_Videos")
wait_for_load()
time.sleep(3)

# Click first video tile
js('''
const firstVideo = document.querySelector('div[role="checkbox"], div[aria-label*="Video"]');
if (firstVideo) {{
    firstVideo.click();
}}
''')
time.sleep(2)

# Trigger download via Shift+D
key_combination("Shift+KeyD")
print("Download triggered via Shift+D")
PY
"""
    print("[*] Navigating to Google Photos videos and initiating download...")
    os.system(cmd)

if __name__ == "__main__":
    main()
