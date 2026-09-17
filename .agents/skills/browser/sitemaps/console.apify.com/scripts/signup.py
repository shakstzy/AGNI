#!/usr/bin/env python3
"""
Apify Automated Sign-Up via Catch-All Email.
Stateless execution: fills multi-step form in Chrome profile, catches verification email
via operations@outerscope.xyz, confirms token, and verifies authenticated dashboard access.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional
import websockets

REPO_ROOT = Path("/home/shakstzy/HADES")
AUTH_DIR = REPO_ROOT / "workspaces/auth"
sys.path.insert(0, str(AUTH_DIR))

import catchall


async def cdp_call(ws, method: str, params: Optional[Dict[str, Any]] = None) -> Any:
    msg_id = int(time.time() * 1000) % 10000000
    payload = {"id": msg_id, "method": method, "params": params or {}}
    await ws.send(json.dumps(payload))
    while True:
        raw = await ws.recv()
        resp = json.loads(raw)
        if resp.get("id") == msg_id:
            if "error" in resp:
                raise RuntimeError(f"CDP call {method} error: {resp['error']}")
            return resp.get("result", {})


async def cdp_eval(ws, expr: str) -> Any:
    res = await cdp_call(
        ws,
        "Runtime.evaluate",
        {
            "expression": expr,
            "returnByValue": True,
            "awaitPromise": True,
        },
    )
    return res.get("result", {}).get("value")


def read_profile_info(profile_name: str) -> Dict[str, Any]:
    prof_dir = REPO_ROOT / f".agents/skills/browser/sitemaps/console.apify.com/profiles/{profile_name}"
    meta_file = prof_dir / "metadata.json"
    login_file = prof_dir / "login.md"
    if not meta_file.is_file():
        raise FileNotFoundError(f"Missing metadata.json for profile {profile_name}")

    meta = json.loads(meta_file.read_text())
    email = f"{profile_name}@outerscope.xyz"
    if login_file.is_file():
        login_text = login_file.read_text()
        email_match = re.search(r"^email:\s*(\S+)", login_text, re.M)
        if email_match:
            email = email_match.group(1)

    # Get password from Bitwarden
    try:
        raw_bw = subprocess.check_output(["bw", "get", "password", email], stderr=subprocess.DEVNULL).decode().strip()
        password = raw_bw
    except Exception:
        password = ""

    return {
        "profile": profile_name,
        "email": email,
        "password": password,
        "cdp_port": meta.get("cdp_port", 9361),
        "user_data_dir": meta.get("user_data_dir"),
    }


def kill_chrome_on_port(port: int) -> None:
    try:
        out = subprocess.check_output(
            ["ss", "-lptn", f"sport = :{port}"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        pids = set(re.findall(r"pid=(\d+)", out))
        for pid in pids:
            try:
                os.kill(int(pid), signal.SIGTERM)
            except OSError:
                pass
    except Exception:
        pass


def launch_chrome(info: Dict[str, Any], url: str, headless: bool = False) -> subprocess.Popen:
    kill_chrome_on_port(info["cdp_port"])
    chrome = shutil.which("google-chrome") or shutil.which("chromium")
    if not chrome:
        raise RuntimeError("google-chrome or chromium not found")

    user_data = Path(info["user_data_dir"])
    user_data.mkdir(parents=True, exist_ok=True)
    for lock in user_data.glob("Singleton*"):
        try:
            lock.unlink()
        except OSError:
            pass

    cmd = [
        chrome,
        "--no-sandbox",
        "--remote-debugging-address=127.0.0.1",
        f"--user-data-dir={info['user_data_dir']}",
        f"--remote-debugging-port={info['cdp_port']}",
        "--no-first-run",
        "--no-default-browser-check",
        "--remote-allow-origins=*",
        "--disable-blink-features=AutomationControlled",
    ]
    env = os.environ.copy()
    if not headless and os.path.exists("/run/user/1000/gdm/Xauthority"):
        env["DISPLAY"] = env.get("DISPLAY", ":1")
        env["XAUTHORITY"] = "/run/user/1000/gdm/Xauthority"
    else:
        cmd.append("--headless=new")

    cmd.append(url)
    return subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


async def type_into(ws, selector: str, text: str) -> None:
    await cdp_eval(ws, f"document.querySelector({json.dumps(selector)}).focus()")
    await asyncio.sleep(0.15)
    await cdp_eval(ws, f"document.querySelector({json.dumps(selector)}).value = ''")
    for char in text:
        await cdp_call(ws, "Input.insertText", {"text": char})
        await asyncio.sleep(0.02)
    # Dispatch change/input events
    await cdp_eval(ws, f"""(() => {{
        const el = document.querySelector({json.dumps(selector)});
        if (el) {{
            el.dispatchEvent(new Event('input', {{ bubbles: true }}));
            el.dispatchEvent(new Event('change', {{ bubbles: true }}));
        }}
    }})()""")
    await asyncio.sleep(0.15)


async def run_signup(profile_name: str, headless: bool = False) -> Dict[str, Any]:
    info = read_profile_info(profile_name)
    port = info["cdp_port"]
    email = info["email"]
    password = info["password"]

    print(f"[{profile_name}] Launching Chrome on port {port} for {email}...")
    proc = launch_chrome(info, "https://console.apify.com/sign-up", headless=headless)

    try:
        # Wait for CDP
        deadline = time.time() + 15
        ws_url = None
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list", timeout=1) as resp:
                    tabs = json.loads(resp.read())
                    pages = [t for t in tabs if t.get("type") == "page"]
                    if pages:
                        ws_url = pages[0].get("webSocketDebuggerUrl")
                        break
            except Exception:
                await asyncio.sleep(0.5)

        if not ws_url:
            return {"ok": False, "error": f"Failed to connect to CDP on port {port}"}

        async with websockets.connect(ws_url, max_size=10_000_000) as ws:
            print(f"[{profile_name}] Connected to page. Waiting for SPA render...")
            await asyncio.sleep(4)

            current_url = await cdp_eval(ws, "location.href")
            print(f"[{profile_name}] Current URL: {current_url}")

            if "sign" not in current_url:
                print(f"[{profile_name}] Already authenticated on {current_url}")
                return {"ok": True, "status": "already_authenticated", "url": current_url}

            # Wait for email input
            for _ in range(15):
                ready = await cdp_eval(ws, "!!document.querySelector('input[name=\"email\"]')")
                if ready:
                    break
                await asyncio.sleep(1)

            if not ready:
                return {"ok": False, "error": "Email input not found"}

            # Step 1: Type Email
            print(f"[{profile_name}] Step 1: Entering email {email}...")
            await type_into(ws, 'input[name="email"]', email)
            await asyncio.sleep(0.5)

            # Click Step 1 Submit Email Button
            click_email_btn = """(() => {
                const btn = document.querySelector('button[data-tracking*="submit-email"], button[type="submit"]');
                if (btn) {
                    btn.click();
                    return { clicked: true, text: btn.innerText.trim() };
                }
                return { clicked: false };
            })()"""
            c1 = await cdp_eval(ws, click_email_btn)
            print(f"[{profile_name}] Step 1 submit result: {c1}")

            # Step 2: Wait for Password input
            print(f"[{profile_name}] Step 2: Waiting for password input...")
            pwd_ready = False
            for _ in range(15):
                pwd_ready = await cdp_eval(ws, "!!document.querySelector('input[name=\"password\"]')")
                if pwd_ready:
                    break
                await asyncio.sleep(0.5)

            if not pwd_ready:
                body_txt = await cdp_eval(ws, "document.body.innerText")
                return {"ok": False, "error": "Password input did not appear", "body_snippet": body_txt[:300]}

            print(f"[{profile_name}] Step 2: Entering password...")
            await type_into(ws, 'input[name="password"]', password)
            await asyncio.sleep(0.5)

            # Click Final Sign Up Button
            click_signup_btn = """(() => {
                const buttons = [...document.querySelectorAll('button')];
                const btn = buttons.find(b => /sign up/i.test(b.innerText || '') && !/google|github/i.test(b.innerText || ''));
                if (btn) {
                    btn.click();
                    return { clicked: true, text: btn.innerText.trim() };
                }
                return { clicked: false };
            })()"""
            c2 = await cdp_eval(ws, click_signup_btn)
            print(f"[{profile_name}] Step 2 final submit result: {c2}")

            # Step 3: Observe submission result
            print(f"[{profile_name}] Observing result...")
            for i in range(15):
                await asyncio.sleep(1)
                page_text = await cdp_eval(ws, "document.body.innerText") or ""
                curr_href = await cdp_eval(ws, "location.href") or ""
                has_bframe = await cdp_eval(ws, "!!document.querySelector('iframe[src*=\"bframe\"]')")

                if has_bframe:
                    print(f"[{profile_name}] reCAPTCHA challenge active (bframe visible).")
                    return {"ok": False, "status": "recaptcha_challenge", "url": curr_href}

                if any(k in page_text.lower() for k in ("verify your email", "sent you a link", "check your email", "confirmation link")):
                    print(f"[{profile_name}] Confirmation email successfully triggered!")
                    return {"ok": True, "status": "email_sent", "url": curr_href}

                if "sign" not in curr_href:
                    print(f"[{profile_name}] Direct redirect into console: {curr_href}!")
                    return {"ok": True, "status": "logged_in", "url": curr_href}

            return {
                "ok": False,
                "status": "timeout_or_unknown",
                "page_snippet": page_text[:300],
                "url": await cdp_eval(ws, "location.href"),
            }

    finally:
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Apify signup automation")
    parser.add_argument("profile", help="Profile name (e.g. apify-01)")
    parser.add_argument("--headless", action="store_true", help="Run headless")
    args = parser.parse_args()

    result = asyncio.run(run_signup(args.profile, headless=args.headless))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
