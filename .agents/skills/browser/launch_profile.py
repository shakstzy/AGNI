#!/usr/bin/env python3
"""Launch a persistent HADES Chrome profile and expose its CDP endpoint."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


def read_metadata(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid profile metadata: {path}") from error
    profile = data.get("user_data_dir")
    if not profile:
        profile = str((path.parent / "user_data").resolve())
        data["user_data_dir"] = profile
    else:
        p = Path(profile)
        if not p.is_absolute():
            profile = str((path.parent / p).resolve())
            data["user_data_dir"] = profile
    os.makedirs(data["user_data_dir"], exist_ok=True)
    for lock in Path(data["user_data_dir"]).glob("Singleton*"):
        try:
            lock.unlink()
        except OSError:
            pass

    port = data.get("cdp_port")
    if not isinstance(port, int):
        cdp = data.get("cdp")
        if isinstance(cdp, str) and cdp:
            parsed = urlparse(cdp)
            if parsed.port:
                port = parsed.port
                data["cdp_port"] = port
    if not isinstance(port, int) or not 1024 <= port <= 65535:
        raise ValueError("profile metadata requires integer cdp_port")
    return data


def profile_command(
    metadata: dict[str, Any], *, headless: bool, chrome: str | None = None, url: str | None = None
) -> list[str]:
    chrome = (
        chrome
        or shutil.which("google-chrome")
        or shutil.which("chromium")
        or "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    )
    if not chrome or not (shutil.which(chrome) or Path(chrome).exists()):
        raise ValueError("Chrome or Chromium is required")
    command = [
        chrome,
        "--no-sandbox",
        "--remote-debugging-address=127.0.0.1",
        f"--user-data-dir={metadata['user_data_dir']}",
        f"--remote-debugging-port={metadata['cdp_port']}",
        "--no-first-run",
        "--no-default-browser-check",
        "--remote-allow-origins=*",
        "--disable-blink-features=AutomationControlled",
    ]
    if headless:
        command.append("--headless=new")
    elif sys.platform != "darwin" and not os.environ.get("DISPLAY"):
        raise ValueError("headed profile launch requires DISPLAY; use the desktop Browser Use host")
    target_url = url.strip() if (url and url.strip()) else "about:blank"
    return [*command, target_url]


def launch(
    metadata: dict[str, Any], *, headless: bool, chrome: str | None = None, url: str | None = None
) -> subprocess.Popen[bytes]:
    return subprocess.Popen(
        profile_command(metadata, headless=headless, chrome=chrome, url=url),
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Launch a persistent Chrome profile exposing CDP.")
    parser.add_argument("metadata", type=Path, help="Path to profile metadata.json")
    parser.add_argument("--headless", action="store_true", help="Launch in headless mode")
    parser.add_argument("--url", default=None, help="Initial URL to launch directly into")
    args = parser.parse_args()

    metadata = read_metadata(args.metadata)
    process = launch(metadata, headless=args.headless, url=args.url)
    print(f"profile Chrome started: pid={process.pid} cdp_port={metadata['cdp_port']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
