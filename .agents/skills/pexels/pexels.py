#!/usr/bin/env python3
"""Pexels photo & video API client for HADES socials and multi-platform pipelines."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

HADES_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = HADES_DIR / ".env"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
API_BASE = "https://api.pexels.com/v1"
VIDEO_API_BASE = "https://api.pexels.com/videos"


def get_api_key() -> str:
    """Retrieve PEXELS_API_KEY from environment, .env file, or Bitwarden."""
    key = os.environ.get("PEXELS_API_KEY")
    if key and key.strip():
        return key.strip()

    if ENV_FILE.is_file():
        for line in ENV_FILE.read_text().splitlines():
            if line.startswith("PEXELS_API_KEY="):
                val = line.split("=", 1)[1].strip()
                if val:
                    return val

    # Fallback to Bitwarden
    try:
        res = subprocess.run(
            ["bw", "get", "item", "pexels.com (adithya@outerscope.xyz)"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if res.returncode == 0:
            item = json.loads(res.stdout)
            for field in item.get("fields", []):
                if field.get("name") == "PEXELS_API_KEY" and field.get("value"):
                    return str(field["value"]).strip()
    except Exception:
        pass

    raise RuntimeError("PEXELS_API_KEY not found in environment, .env, or Bitwarden")


def _request(url: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    key = api_key or get_api_key()
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": key,
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def search_photos(
    query: str,
    count: int = 5,
    orientation: Optional[str] = None,
    size: Optional[str] = None,
    api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Search Pexels for photos.
    orientation: 'landscape', 'portrait', 'square'
    size: 'large', 'medium', 'small'
    """
    params: Dict[str, Any] = {"query": query, "per_page": count}
    if orientation:
        params["orientation"] = orientation
    if size:
        params["size"] = size

    qs = urllib.parse.urlencode(params)
    url = f"{API_BASE}/search?{qs}"
    data = _request(url, api_key=api_key)
    return data.get("photos", [])


def search_videos(
    query: str,
    count: int = 5,
    orientation: Optional[str] = None,
    size: Optional[str] = None,
    api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Search Pexels for videos."""
    params: Dict[str, Any] = {"query": query, "per_page": count}
    if orientation:
        params["orientation"] = orientation
    if size:
        params["size"] = size

    qs = urllib.parse.urlencode(params)
    url = f"{VIDEO_API_BASE}/search?{qs}"
    data = _request(url, api_key=api_key)
    return data.get("videos", [])


def download_file(url: str, dest_path: Path) -> Path:
    """Download a photo or video asset directly to a file."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp, open(dest_path, "wb") as f:
        while chunk := resp.read(65536):
            f.write(chunk)
    return dest_path


def search_and_download(
    query: str,
    dest_dir: Path | str,
    count: int = 3,
    orientation: Optional[str] = None,
    size_field: str = "large2x",
    prefix: str = "img",
) -> List[Dict[str, Any]]:
    """
    Search and download photos directly into a directory.
    Returns list of dicts with file path, photographer, and attribution URL.
    """
    target_dir = Path(dest_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    photos = search_photos(query=query, count=count, orientation=orientation)
    downloaded = []

    for i, photo in enumerate(photos):
        src_map = photo.get("src", {})
        img_url = src_map.get(size_field) or src_map.get("large") or src_map.get("original")
        if not img_url:
            continue
        photo_id = photo.get("id", i)
        ext = "jpg"
        clean_prefix = "".join(c if c.isalnum() or c in "-_" else "_" for c in prefix).strip("_")
        out_name = f"{clean_prefix}_{photo_id}.{ext}" if clean_prefix else f"pexels_{photo_id}.{ext}"
        out_file = target_dir / out_name
        download_file(img_url, out_file)
        downloaded.append(
            {
                "id": photo_id,
                "file": str(out_file),
                "url": photo.get("url"),
                "photographer": photo.get("photographer"),
                "photographer_url": photo.get("photographer_url"),
                "alt": photo.get("alt", ""),
            }
        )

    return downloaded


def main() -> None:
    parser = argparse.ArgumentParser(description="Pexels stock media fetcher for HADES")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # Search
    s_p = sub.add_parser("search", help="Search photos")
    s_p.add_argument("query", help="Search query")
    s_p.add_argument("--count", "-c", type=int, default=5, help="Number of items")
    s_p.add_argument("--orientation", "-o", choices=["landscape", "portrait", "square"])
    s_p.add_argument("--json", action="store_true", help="Output full JSON")

    # Download
    d_p = sub.add_parser("download", help="Search and download photos")
    d_p.add_argument("query", help="Search query")
    d_p.add_argument("--out", "-o", required=True, help="Destination directory or file")
    d_p.add_argument("--count", "-c", type=int, default=3, help="Number of photos")
    d_p.add_argument("--orientation", choices=["landscape", "portrait", "square"])
    d_p.add_argument("--size", default="large2x", choices=["original", "large2x", "large", "medium", "small"])
    d_p.add_argument("--prefix", default="", help="File prefix")

    args = parser.parse_args()

    if args.cmd == "search":
        photos = search_photos(args.query, count=args.count, orientation=args.orientation)
        if args.json:
            print(json.dumps(photos, indent=2))
        else:
            for p in photos:
                print(f"[{p.get('id')}] {p.get('alt') or args.query} by {p.get('photographer')}")
                print(f"  URL: {p.get('url')}")
                print(f"  Img: {p.get('src', {}).get('large')}\n")

    elif args.cmd == "download":
        res = search_and_download(
            query=args.query,
            dest_dir=args.out,
            count=args.count,
            orientation=args.orientation,
            size_field=args.size,
            prefix=args.prefix,
        )
        print(f"Successfully downloaded {len(res)} images to {args.out}:")
        for item in res:
            print(f"  - {item['file']} ({item['photographer']})")


if __name__ == "__main__":
    main()
