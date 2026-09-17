"""Parallel multi-address ingest with per-domain rate limiting.

Cross-site parallelism per address is free (different WAFs).
Within a site, cap at 2 concurrent + 1.5s gap between request entries.
Per-event-loop limiters so a second asyncio.run() doesn't crash.
"""
from __future__ import annotations

import asyncio
import json
import sys
import time
from typing import Any, Callable

import lookup
import redfin
import zillow
import rent_estimate


class _DomainLimiter:
    def __init__(self, *, concurrent: int, min_gap: float):
        self.sem = asyncio.Semaphore(concurrent)
        self.min_gap = min_gap
        self.next_allowed_at = 0.0
        self._lock = asyncio.Lock()

    async def __aenter__(self):
        await self.sem.acquire()
        async with self._lock:
            now = time.monotonic()
            wait = self.next_allowed_at - now
            start = max(now, self.next_allowed_at)
            self.next_allowed_at = start + self.min_gap
        if wait > 0:
            await asyncio.sleep(wait)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.sem.release()


_LIMITER_CACHE: dict[int, dict[str, "_DomainLimiter"]] = {}


def _limiters_for_current_loop() -> dict[str, "_DomainLimiter"]:
    loop = asyncio.get_running_loop()
    key = id(loop)
    cached = _LIMITER_CACHE.get(key)
    if cached is None:
        cached = {
            "redfin": _DomainLimiter(concurrent=2, min_gap=1.5),
            "zillow": _DomainLimiter(concurrent=2, min_gap=2.0),
        }
        _LIMITER_CACHE[key] = cached
    return cached


async def _run_in_thread(fn: Callable[..., Any], *args, **kwargs):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: fn(*args, **kwargs))


async def _safe_redfin_property(url: str, *, include_raw: bool = False) -> dict:
    async with _limiters_for_current_loop()["redfin"]:
        try:
            return await _run_in_thread(redfin.property_details, url, include_raw=include_raw)
        except Exception as e:
            return {"error": str(e), "url": url, "source": "redfin"}


async def _safe_zillow_property(url: str, *, include_raw: bool = False) -> dict:
    async with _limiters_for_current_loop()["zillow"]:
        try:
            return await _run_in_thread(zillow.property_details, url, include_raw=include_raw)
        except Exception as e:
            return {"error": str(e), "url": url, "source": "zillow"}


async def _resolve_zillow_url(address: str) -> str | None:
    async with _limiters_for_current_loop()["zillow"]:
        return await _run_in_thread(lookup.find_zillow_url, address)


async def _resolve_redfin_url(address: str) -> str | None:
    """Redfin URL resolution hits Redfin's own autocomplete, so it counts
    against the Redfin domain limiter.
    """
    async with _limiters_for_current_loop()["redfin"]:
        return await _run_in_thread(lookup.find_redfin_url, address)


async def _safe_lookup(address: str, *, include_raw: bool = False,
                        redfin_url: str | None = None,
                        zillow_url: str | None = None) -> dict:
    rf_url = redfin_url or await _resolve_redfin_url(address)
    zw_url = zillow_url or await _resolve_zillow_url(address)

    rf_task = _safe_redfin_property(rf_url, include_raw=include_raw) if rf_url else \
              _aresult({"error": "no Redfin URL found via autocomplete."})
    zw_task = _safe_zillow_property(zw_url, include_raw=include_raw) if zw_url else \
              _aresult({"error": "no Zillow URL found via slug redirect."})

    rf, zw = await asyncio.gather(rf_task, zw_task)
    aggregate, comparison = lookup._aggregate_views(rf, zw)
    rf_addr = (rf.get("address") or "") if isinstance(rf, dict) else ""
    zw_addr = (zw.get("address") or "") if isinstance(zw, dict) else ""
    addr_match = "ok"
    if rf_addr and zw_addr and rf_addr.split(",")[0].strip().lower() != zw_addr.split(",")[0].strip().lower():
        addr_match = "mismatch"
    if rf.get("error") and zw.get("error"):
        addr_match = "neither_resolved"
    elif rf.get("error") or zw.get("error"):
        addr_match = "single_source"
    return {
        "input_address": address,
        "redfin_url": rf_url, "zillow_url": zw_url,
        "address_match": addr_match,
        "redfin": rf, "zillow": zw,
        "aggregate": aggregate, "comparison": comparison,
    }


async def _aresult(d: dict) -> dict:
    return d


async def _gather(coros, *, total_concurrency: int = 8) -> list[dict]:
    sem = asyncio.Semaphore(total_concurrency)

    async def wrapped(c):
        async with sem:
            return await c

    return await asyncio.gather(*(wrapped(c) for c in coros))


def gather_lookups(addresses: list[str], *,
                   total_concurrency: int = 8,
                   include_raw: bool = False) -> list[dict]:
    async def _main():
        coros = [_safe_lookup(a, include_raw=include_raw) for a in addresses]
        return await _gather(coros, total_concurrency=total_concurrency)
    return asyncio.run(_main())


def gather_rent_estimates(addresses: list[str], *,
                          radius_miles: float = 1.0,
                          beds_tolerance: int = 0,
                          total_concurrency: int = 8) -> list[dict]:
    async def _main():
        coros = [
            _run_in_thread(
                rent_estimate.estimate_rent, a,
                radius_miles=radius_miles, beds_tolerance=beds_tolerance,
            ) for a in addresses
        ]
        return await _gather(coros, total_concurrency=total_concurrency)
    return asyncio.run(_main())


async def _safe_cashflow(address: str, **kwargs) -> dict:
    try:
        import cashflow
        return await _run_in_thread(cashflow.run, address, save=kwargs.get("save", False), **kwargs)
    except Exception as e:
        return {"error": str(e), "address": address, "source": "cashflow"}


async def _safe_parcel(address: str, **kwargs) -> dict:
    try:
        import parcel
        import lookup
        lk = await _run_in_thread(lookup.lookup, address)
        agg = (lk or {}).get("aggregate") or {}
        price = kwargs.get("price") or agg.get("price")
        lot_sqft = agg.get("lot_size") or agg.get("lot_sqft") or 5200.0
        year_built = agg.get("year_built") or 1920
        beds = agg.get("beds") or 4
        baths = agg.get("baths") or 2.0
        sqft = agg.get("sqft") or 2000.0
        tax_assessed = agg.get("tax_assessed_value")
        annual_tax = agg.get("annual_property_tax")
        units = kwargs.get("units") or 2
        return await _run_in_thread(
            parcel.analyze_parcel,
            address=address,
            price=price,
            lot_sqft=lot_sqft,
            year_built=year_built,
            units=units,
            beds=beds,
            baths=baths,
            sqft=sqft,
            tax_assessed_value=tax_assessed,
            historical_annual_tax=annual_tax,
        )
    except Exception as e:
        return {"error": str(e), "address": address, "source": "parcel"}


def gather_cashflows(addresses: list[str], *, total_concurrency: int = 4, **kwargs) -> list[dict]:
    async def _main():
        coros = [_safe_cashflow(a, **kwargs) for a in addresses]
        return await _gather(coros, total_concurrency=total_concurrency)
    return asyncio.run(_main())


def gather_parcels(addresses: list[str], *, total_concurrency: int = 4, **kwargs) -> list[dict]:
    async def _main():
        coros = [_safe_parcel(a, **kwargs) for a in addresses]
        return await _gather(coros, total_concurrency=total_concurrency)
    return asyncio.run(_main())


def _read_addresses(path: str) -> list[str]:
    with open(path) as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


def _emit_ndjson(rows: list[dict]) -> None:
    for r in rows:
        json.dump(r, sys.stdout, default=str)
        sys.stdout.write("\n")


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(prog="batch")
    sub = ap.add_subparsers(dest="cmd", required=True)

    lp = sub.add_parser("lookup", help="run `re lookup` for each address; output NDJSON")
    lp.add_argument("addresses_file", help="path to a text file with one address per line")
    lp.add_argument("--include-raw", action="store_true")
    lp.add_argument("--total-concurrency", type=int, default=8,
                    help="cap on simultaneous in-flight tasks (per-domain caps still apply)")

    rp = sub.add_parser("rent-estimate", help="run `re rent-estimate` for each address; output NDJSON")
    rp.add_argument("addresses_file")
    rp.add_argument("--radius-miles", type=float, default=1.0)
    rp.add_argument("--beds-tolerance", type=int, default=0)
    rp.add_argument("--total-concurrency", type=int, default=8)

    cp = sub.add_parser("cashflow", help="run `re cashflow` for each address; output NDJSON")
    cp.add_argument("addresses_file")
    cp.add_argument("--total-concurrency", type=int, default=4)
    cp.add_argument("--save", action="store_true", help="save markdown dossier to properties dir")

    pp = sub.add_parser("parcel", help="run `re parcel` for each address; output NDJSON")
    pp.add_argument("addresses_file")
    pp.add_argument("--total-concurrency", type=int, default=4)

    args = ap.parse_args(argv)
    addresses = _read_addresses(args.addresses_file)
    if not addresses:
        print("no addresses in file", file=sys.stderr)
        return 1

    if args.cmd == "lookup":
        rows = gather_lookups(addresses,
                              include_raw=args.include_raw,
                              total_concurrency=args.total_concurrency)
    elif args.cmd == "rent-estimate":
        rows = gather_rent_estimates(addresses,
                                     radius_miles=args.radius_miles,
                                     beds_tolerance=args.beds_tolerance,
                                     total_concurrency=args.total_concurrency)
    elif args.cmd == "cashflow":
        rows = gather_cashflows(addresses,
                                total_concurrency=args.total_concurrency,
                                save=args.save)
    elif args.cmd == "parcel":
        rows = gather_parcels(addresses,
                              total_concurrency=args.total_concurrency)
    else:
        return 1
    _emit_ndjson(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
