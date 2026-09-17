#!/usr/bin/env python3
"""HUD Fair Market Rent (FMR) lookup by ZIP -> {bedrooms: monthly rent}.

FMR is the backbone of the Section 8 analysis (see section8.py): it's HUD's
per-bedroom rent benchmark for an area, and the local PHA's voucher payment
standard is set at 90-110% of it.

Two backends, auto-selected:

  1. No-token (default).  Downloads HUD's annual Small Area FMR spreadsheet
     (ZIP-level rents for every designated SAFMR metro -- which is where this
     cheap-multifamily-on-Section-8 strategy operates) and caches it locally.
     Parsed with the Python standard library only (no pandas/openpyxl). Works
     with zero credentials. Coverage is SAFMR metros; a ZIP outside SAFMR
     coverage returns a clear degraded result unless a token is set.

  2. Token (optional).  If a HUD API token is supplied (arg or $HUD_API_TOKEN),
     uses the live HUD User API, which adds national county-level fallback for
     non-SAFMR ZIPs. Free token: https://www.huduser.gov/hudapi/public/register

Result schema (the stable contract section8.py / cashflow.py depend on):
    {"ok": True, "zip": "44105", "fiscal_year": 2026,
     "area_name": "Cleveland-Elyria, OH MSA", "source": "safmr-bulk",
     "is_small_area": True, "fmr": {0: 800, 1: 870, 2: 1016, 3: 1304, 4: 1537}}
"""

from __future__ import annotations

import argparse
import datetime as _dt
import io
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from typing import Any

import _env

_CACHE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", ".cache", "fmr"
)
_XLSX_NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
_IMPERSONATE = "chrome124"
# HUD's WAF blocks bare clients; curl_cffi's impersonation handles the TLS/UA
# fingerprint, and a Referer keeps the static-file server happy.
_DL_HEADERS = {"Referer": "https://www.huduser.gov/"}


# --------------------------------------------------------------------------- #
# Fiscal year + URLs
# --------------------------------------------------------------------------- #
def _current_fy(today: _dt.date | None = None) -> int:
    """Federal fiscal year (Oct 1 - Sep 30). FY2026 = Oct 2025 - Sep 2026."""
    d = today or _dt.date.today()
    return d.year + 1 if d.month >= 10 else d.year


def _safmr_urls(year: int) -> list[str]:
    base = f"https://www.huduser.gov/portal/datasets/fmr/fmr{year}"
    return [
        f"{base}/fy{year}_safmrs_revised.xlsx",  # revised supersedes the original
        f"{base}/fy{year}_safmrs.xlsx",
    ]


# --------------------------------------------------------------------------- #
# Minimal, dependency-free .xlsx reader (column-letter aware -> sparse-safe)
# --------------------------------------------------------------------------- #
def _col_to_idx(ref: str) -> int:
    letters = "".join(ch for ch in ref if ch.isalpha())
    idx = 0
    for ch in letters:
        idx = idx * 26 + (ord(ch.upper()) - 64)
    return idx - 1


def _first_sheet_name(zf: zipfile.ZipFile) -> str:
    for name in zf.namelist():
        if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", name):
            return name
    return "xl/worksheets/sheet1.xml"


def _read_xlsx_rows(data: bytes) -> list[dict[int, str]]:
    """Return each row as {column_index: cell_text}. Empty cells are omitted."""
    zf = zipfile.ZipFile(io.BytesIO(data))
    try:
        ss = ET.fromstring(zf.read("xl/sharedStrings.xml"))
        strings = [
            "".join(t.text or "" for t in si.findall(".//s:t", _XLSX_NS))
            for si in ss.findall("s:si", _XLSX_NS)
        ]
    except KeyError:
        strings = []
    sheet = ET.fromstring(zf.read(_first_sheet_name(zf)))
    rows: list[dict[int, str]] = []
    for row in sheet.findall(".//s:row", _XLSX_NS):
        cells: dict[int, str] = {}
        auto = 0
        for c in row.findall("s:c", _XLSX_NS):
            ref = c.get("r") or ""
            ci = _col_to_idx(ref) if ref else auto
            auto = ci + 1
            v = c.find("s:v", _XLSX_NS)
            if v is None or v.text is None:
                continue
            cells[ci] = strings[int(v.text)] if c.get("t") == "s" else v.text
        rows.append(cells)
    return rows


def _norm_header(s: str | None) -> str:
    return re.sub(r"\s+", " ", (s or "").strip()).upper()


# --------------------------------------------------------------------------- #
# Bulk SAFMR backend (no token)
# --------------------------------------------------------------------------- #
def _download(url: str) -> bytes | None:
    from curl_cffi import requests as curl_requests

    try:
        r = curl_requests.get(
            url, headers=_DL_HEADERS, impersonate=_IMPERSONATE, timeout=60
        )
    except Exception:
        return None
    if r.status_code != 200 or not r.content or len(r.content) < 1024:
        return None
    # xlsx is a zip; first bytes are "PK"
    if r.content[:2] != b"PK":
        return None
    return r.content


def _parse_safmr(data: bytes) -> tuple[dict[str, dict[str, Any]], str]:
    rows = _read_xlsx_rows(data)
    if not rows:
        raise ValueError("empty SAFMR workbook")
    header = rows[0]
    by_name = {_norm_header(v): k for k, v in header.items()}

    def find(*names: str, default: int | None = None) -> int | None:
        for n in names:
            if n in by_name:
                return by_name[n]
        return default

    zip_col = find("ZIP CODE", "ZIPCODE", default=0)
    area_col = next((k for name, k in by_name.items() if "AREA NAME" in name), 2)
    bed_cols: dict[int, int] = {}
    # positional fallback: ZIP=0, area=2, rents at 3,6,9,12,15 (each BR trailed by
    # its 90%/110% payment-standard columns)
    fallback = {0: 3, 1: 6, 2: 9, 3: 12, 4: 15}
    for b in range(5):
        col = find(f"SAFMR {b}BR", f"SAFMR{b}BR", default=fallback[b])
        bed_cols[b] = col

    db: dict[str, dict[str, Any]] = {}
    detected_fy = ""
    for r in rows[1:]:
        raw_zip = r.get(zip_col)
        if not raw_zip:
            continue
        zip5 = re.sub(r"\D", "", str(raw_zip)).zfill(5)[:5]
        if len(zip5) != 5:
            continue
        fmr: dict[int, int] = {}
        for b, col in bed_cols.items():
            val = r.get(col)
            if val is None:
                continue
            try:
                fmr[b] = int(round(float(str(val).replace(",", "").replace("$", ""))))
            except (TypeError, ValueError):
                continue
        if not fmr:
            continue
        db[zip5] = {"area": (r.get(area_col) or "").strip(), "fmr": fmr}
    return db, detected_fy


def _cache_path(year: int) -> str:
    return os.path.join(_CACHE_DIR, f"safmr_{year}.json")


def _load_safmr_db(
    year: int, *, refresh: bool = False
) -> tuple[dict[str, dict[str, Any]], int]:
    """Return (db, fiscal_year_used). Tries `year`, then year-1. Caches parsed JSON."""
    for fy in (year, year - 1):
        path = _cache_path(fy)
        if not refresh and os.path.exists(path):
            try:
                with open(path) as f:
                    cached = json.load(f)
                # JSON keys are strings; normalize fmr bed keys back to int on read
                return cached, fy
            except (json.JSONDecodeError, OSError):
                pass
        for url in _safmr_urls(fy):
            data = _download(url)
            if data is None:
                continue
            try:
                db, _ = _parse_safmr(data)
            except (ValueError, ET.ParseError, KeyError):
                continue
            if not db:
                continue
            os.makedirs(_CACHE_DIR, exist_ok=True)
            tmp = path + ".tmp"
            with open(tmp, "w") as f:
                json.dump(db, f)
            os.replace(tmp, path)
            return db, fy
    return {}, year


def _bulk_lookup(zip_code: str, year: int, refresh: bool) -> dict[str, Any]:
    db, fy = _load_safmr_db(year, refresh=refresh)
    if not db:
        return {
            "ok": False,
            "zip": zip_code,
            "error": "could not download/parse HUD SAFMR data (network or WAF); "
            "retry, or set a HUD_API_TOKEN for the API path",
        }
    row = db.get(zip_code)
    if not row:
        return {
            "ok": False,
            "zip": zip_code,
            "fiscal_year": fy,
            "source": "safmr-bulk",
            "error": f"ZIP {zip_code} not in HUD Small Area FMR coverage for FY{fy} "
            "(non-SAFMR area); set HUD_API_TOKEN for county-level FMR fallback",
        }
    fmr = {int(k): int(v) for k, v in row["fmr"].items()}
    return {
        "ok": True,
        "zip": zip_code,
        "fiscal_year": fy,
        "area_name": row.get("area") or None,
        "source": "safmr-bulk",
        "is_small_area": True,
        "fmr": fmr,
    }


# --------------------------------------------------------------------------- #
# HUD API backend (optional token; adds national county fallback)
# --------------------------------------------------------------------------- #
_API_BED_KEYS = {
    0: "Efficiency",
    1: "One-Bedroom",
    2: "Two-Bedroom",
    3: "Three-Bedroom",
    4: "Four-Bedroom",
}


def _api_get(url: str, token: str, params: dict[str, Any]) -> dict[str, Any] | None:
    from curl_cffi import requests as curl_requests

    try:
        r = curl_requests.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            impersonate=_IMPERSONATE,
            timeout=45,
        )
    except Exception:
        return None
    if r.status_code != 200:
        return None
    try:
        return r.json()
    except ValueError:
        return None


def _row_to_fmr(row: dict[str, Any]) -> dict[int, int]:
    fmr: dict[int, int] = {}
    for b, key in _API_BED_KEYS.items():
        val = row.get(key)
        if val in (None, ""):
            continue
        try:
            fmr[b] = int(round(float(str(val).replace(",", ""))))
        except (TypeError, ValueError):
            continue
    return fmr


def _api_lookup(zip_code: str, year: int, token: str) -> dict[str, Any]:
    # ZIP -> county FIPS via the HUD USPS crosswalk (type=2). HUD's FMR data
    # endpoint keys on the county entity id `{county_fips}99999`; for a SAFMR
    # county the payload still carries per-ZIP small-area rows, so this one call
    # covers both SAFMR and non-SAFMR ZIPs. (The bulk SAFMR file is primary --
    # see lookup() -- so in practice this path runs only for non-SAFMR ZIPs.)
    cross = _api_get(
        "https://www.huduser.gov/hudapi/public/usps",
        token,
        {"type": 2, "query": zip_code},
    )
    fips = None
    if cross:
        results = (cross.get("data") or {}).get("results") or []
        if results:
            best = max(results, key=lambda x: float(x.get("res_ratio") or 0))
            fips = best.get("geoid") or best.get("county")
    if not fips:
        return {
            "ok": False,
            "zip": zip_code,
            "error": "HUD crosswalk could not map ZIP -> county (check token)",
        }

    # The API lags the bulk file by a fiscal year (the current FY isn't published
    # on the API while the bulk SAFMR file already carries it), so try the
    # requested year and fall back one year on an empty/404 response.
    entity = f"{fips}99999"
    payload = None
    fy_used = year
    for fy in (year, year - 1):
        payload = _api_get(
            f"https://www.huduser.gov/hudapi/public/fmr/data/{entity}",
            token,
            {"year": fy},
        )
        if payload:
            fy_used = fy
            break
    if not payload:
        return {
            "ok": False,
            "zip": zip_code,
            "error": f"HUD FMR API returned no data for county {fips}",
        }
    data = payload.get("data") or {}
    is_small = str(data.get("smallarea_status")) == "1"
    area_name = data.get("metro_name") or data.get("county_name")
    basic = data.get("basicdata") or []
    if isinstance(basic, dict):
        basic = [basic]

    row = None
    if is_small:
        row = next((b for b in basic if str(b.get("zip_code")) == zip_code), None)
    if row is None and basic:
        row = basic[0]  # area-wide record for non-SAFMR areas
        is_small = is_small and str(row.get("zip_code")) == zip_code
    if row is None:
        return {"ok": False, "zip": zip_code, "error": "no FMR record in API payload"}

    fmr = _row_to_fmr(row)
    if not fmr:
        return {
            "ok": False,
            "zip": zip_code,
            "error": "API record had no bedroom rents",
        }
    return {
        "ok": True,
        "zip": zip_code,
        "fiscal_year": int(row.get("year") or fy_used),
        "area_name": area_name,
        "source": "hud-api",
        "is_small_area": bool(is_small),
        "fmr": fmr,
    }


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #
def lookup(
    zip_code: str,
    *,
    year: int | None = None,
    token: str | None = None,
    refresh: bool = False,
) -> dict[str, Any]:
    """ZIP -> FMR schedule. Uses the HUD API when a token is given, else the
    no-token bulk SAFMR file. Returns the result schema documented at module top."""
    zip_code = re.sub(r"\D", "", str(zip_code)).zfill(5)[:5]
    if len(zip_code) != 5:
        return {"ok": False, "zip": zip_code, "error": "invalid ZIP (need 5 digits)"}
    year = year or _current_fy()
    _env.ensure_loaded()
    token = token or os.environ.get("HUD_API_TOKEN")

    # Bulk SAFMR file is primary: it's cached, fast, carries the newest fiscal
    # year, and covers every SAFMR metro this strategy targets. A token only adds
    # the county-level API fallback for ZIPs the bulk file doesn't cover.
    bulk = _bulk_lookup(zip_code, year, refresh)
    if bulk.get("ok"):
        return bulk
    if token:
        api = _api_lookup(zip_code, year, token)
        if api.get("ok"):
            return api
    return bulk


def main(argv=None):
    ap = argparse.ArgumentParser(prog="fmr", description="HUD Fair Market Rent by ZIP")
    ap.add_argument("zip", help="5-digit ZIP code")
    ap.add_argument(
        "--year", type=int, help="FMR fiscal year (default: current federal FY)"
    )
    ap.add_argument(
        "--hud-token",
        help="HUD API token (else $HUD_API_TOKEN, else no-token bulk file)",
    )
    ap.add_argument(
        "--refresh",
        action="store_true",
        help="ignore cache; re-download the SAFMR file",
    )
    args = ap.parse_args(argv)
    res = lookup(args.zip, year=args.year, token=args.hud_token, refresh=args.refresh)
    json.dump(res, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
