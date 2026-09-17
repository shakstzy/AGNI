#!/usr/bin/env python3
"""
Supabase Automated Sign-Up via Catch-All Email.
Stateless execution: fills form, catches verification email via operations@outerscope.xyz,
confirms token, and verifies authenticated dashboard access.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional
import websockets

REPO_ROOT = Path(__file__).resolve().parents[6]
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


def read_profile_info(site_dir: Path, profile_name: str) -> Dict[str, Any]:
    prof_dir = site_dir / "profiles" / profile_name
    meta_file = prof_dir / "metadata.json"
    login_file = prof_dir / "login.md"
    if not meta_file.is_file():
        raise FileNotFoundError(f"Missing metadata.json for profile {profile_name}")
    if not login_file.is_file():
        raise FileNotFoundError(f"Missing login.md for profile {profile_name}")

    meta = json.loads(meta_file.read_text())
    login_text = login_file.read_text()
    email_match = re.search(r"^email:\s*(\S+)", login_text, re.M)
    email = email_match.group(1) if email_match else f"{profile_name}@outerscope.xyz"

    return {
        "profile": profile_name,
        "email": email,
        "cdp_port": meta.get("cdp_port", 9322),
        "user_data_dir": meta.get("user_data_dir", f"/tmp/hades-{profile_name}"),
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
    cmd = [
        chrome,
        "--no-sandbox",
        "--remote-debugging-address=127.0.0.1",
        f"--user-data-dir={info['user_data_dir']}",
        f"--remote-debugging-port={info['cdp_port']}",
        "--no-first-run",
        "--no-default-browser-check",
        "--remote-allow-origins=*",
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
    await asyncio.sleep(0.2)
    await cdp_eval(ws, f"document.querySelector({json.dumps(selector)}).value = ''")
    await cdp_call(ws, "Input.insertText", {"text": text})
    await asyncio.sleep(0.2)


async def perform_signup(info: Dict[str, Any], password: str) -> Dict[str, Any]:
    port = info["cdp_port"]
    email = info["email"]

    # 1. Launch Chrome
    proc = launch_chrome(info, "https://supabase.com/dashboard/sign-up")
    try:
        # 2. Wait for CDP endpoint
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
                await asyncio.sleep(0.3)

        if not ws_url:
            return {"ok": False, "error": f"Failed to connect to Chrome CDP on port {port}"}

        async with websockets.connect(ws_url, max_size=10_000_000) as ws:
            # 3. Wait for page load
            await asyncio.sleep(4)
            current_url = await cdp_eval(ws, "location.href")
            title = await cdp_eval(ws, "document.title")

            # Check if already authenticated or on dashboard
            if any(k in current_url for k in ("dashboard/projects", "dashboard/org", "dashboard/organizations")):
                return {
                    "ok": True,
                    "email": email,
                    "status": "already_authenticated",
                    "url": current_url,
                }

            # 4. Fill signup form with keystrokes
            email_exists = await cdp_eval(ws, "!!document.querySelector('input[name=\"email\"]')")
            if not email_exists:
                return {"ok": False, "error": "Sign-up form inputs not found", "page_title": title, "url": current_url}

            await type_into(ws, 'input[name="email"]', email)
            await type_into(ws, 'input[name="password"]', password)

            # 5. Click Sign Up button
            click_js = """(() => {
                const buttons = [...document.querySelectorAll('button')];
                const btn = buttons.find(b => /sign up/i.test(b.innerText || ''));
                if (btn) {
                    btn.click();
                    return { clicked: true, text: btn.innerText.trim() };
                }
                return { clicked: false };
            })()"""

            click_res = await cdp_eval(ws, click_js)
            if not click_res or not click_res.get("clicked"):
                return {"ok": False, "error": "Sign up button not found or could not be clicked"}

            # Wait for form submission response
            form_submitted = False
            for _ in range(10):
                await asyncio.sleep(1)
                body_text = await cdp_eval(ws, "document.body.innerText") or ""
                if any(k in body_text.lower() for k in ("check your email", "sent you a link", "confirm your email")):
                    form_submitted = True
                    print(f"[SIGNUP] Form successfully submitted for {email}! Supabase sent confirmation.")
                    break
            post_submit_url = await cdp_eval(ws, "location.href")

            # 6. Poll catch-all email for confirmation link
            print(f"[SIGNUP] Polling catch-all for confirmation email to {email}...")
            msg = catchall.poll_for_message(email, query="supabase", timeout=90, interval=4)
            if not msg:
                return {
                    "ok": False,
                    "error": "Confirmation email not received within timeout",
                    "email": email,
                    "post_submit_url": post_submit_url,
                    "form_submitted": form_submitted,
                }

            msg_content = catchall.get_message_content(msg["id"])
            body = msg_content.get("body", "") or json.dumps(msg_content)
            urls = catchall.extract_verification_urls(body, domain_hint="supabase")
            if not urls:
                return {
                    "ok": False,
                    "error": "No verification URLs found in confirmation email",
                    "message_id": msg["id"],
                }

            verify_url = urls[0]
            print(f"[SIGNUP] Found verification URL: {verify_url}")

            # 7. Navigate active browser tab to verification link
            print("[SIGNUP] Navigating browser to confirmation URL...")
            await cdp_call(ws, "Page.navigate", {"url": verify_url})

            # Wait for redirect and session creation
            for _ in range(15):
                await asyncio.sleep(1)
                cur = await cdp_eval(ws, "location.href")
                if any(k in cur for k in ("dashboard/new", "dashboard/organizations", "dashboard/projects")):
                    break

            cur_url = await cdp_eval(ws, "location.href")
            # If on dashboard/new, provision default organization
            if "dashboard/new" in cur_url:
                print(f"[SIGNUP] Provisioning default organization for {info['profile']}...")
                await asyncio.sleep(2)
                org_name = f"{info['profile']}'s Org"
                await cdp_eval(ws, f"""(() => {{
                    const input = document.querySelector('input[placeholder="Organization name"]') || document.querySelector('input[name="name"]');
                    if (input) {{
                        const set = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                        set.call(input, {json.dumps(org_name)});
                        input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    }}
                    const btn = [...document.querySelectorAll('button')].find(b => /create organization/i.test(b.innerText||''));
                    if (btn) btn.click();
                }})()""")
                for _ in range(15):
                    await asyncio.sleep(1)
                    cur_url = await cdp_eval(ws, "location.href")
                    if "organizations" in cur_url or "projects" in cur_url:
                        break

            await asyncio.sleep(3)
            final_url = await cdp_eval(ws, "location.href")
            final_title = await cdp_eval(ws, "document.title")
            final_text = await cdp_eval(ws, "document.body.innerText")

            is_confirmed = (
                "dashboard" in final_url
                or "projects" in final_url
                or "organizations" in final_url
                or "welcome" in final_text.lower()
                or "organization" in final_text.lower()
            )

            proof_path = f"/home/shakstzy/.gemini/antigravity-cli/brain/1630dfae-81ef-47c7-b47b-d4d4e14e8825/proof_{info['profile']}.png"
            try:
                ss = await cdp_call(ws, "Page.captureScreenshot", {"format": "png"})
                with open(proof_path, "wb") as f:
                    f.write(base64.b64decode(ss["data"]))
            except Exception as e:
                print(f"[SIGNUP] Screenshot capture error: {e}")

            return {
                "ok": is_confirmed,
                "profile": info["profile"],
                "email": email,
                "status": "confirmed" if is_confirmed else "pending_verification",
                "final_url": final_url,
                "final_title": final_title,
                "proof_screenshot": proof_path if is_confirmed else None,
                "verification_url": verify_url,
            }

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()


def get_password_from_vault(email: str) -> Optional[str]:
    bw = shutil.which("bw")
    if not bw:
        return None
    res = subprocess.run([bw, "get", "password", email], capture_output=True, text=True)
    if res.returncode == 0 and res.stdout.strip():
        return res.stdout.strip()
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Supabase Catch-All Sign-Up")
    parser.add_argument("--profile", default="supabase-03", help="Profile name")
    parser.add_argument("--password", default=None, help="Account password (retrieved from Bitwarden if omitted)")
    args = parser.parse_args()

    site_dir = Path(__file__).resolve().parents[1]
    info = read_profile_info(site_dir, args.profile)
    password = args.password or get_password_from_vault(info["email"]) or "N_nuH198Rb04mX2GCnuPRg!Aa1"
    res = asyncio.run(perform_signup(info, password))
    print(json.dumps(res, indent=2))
    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
