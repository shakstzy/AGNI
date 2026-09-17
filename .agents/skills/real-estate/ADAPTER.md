# Real Estate Research Adapter

The Real Estate adapter provides native CLI execution against Redfin and Zillow scrapers without requiring API keys or headless browsers.

## Operating Contract

- **Binary / Entry**: `.agents/skills/local/real-estate/re` or ambient `re` in PATH (symlinked to `/home/shakstzy/.local/bin/re`).
- **Core Scripts**: `.agents/skills/local/real-estate/scripts/` (`lookup.py`, `redfin.py`, `redfin_parse.py`, `zillow.py`, `zillow_parse.py`, `rent_estimate.py`, `cashflow.py`, `batch.py`, `dedupe.py`).
- **Runtime**: `uv run --quiet python` executing within python >=3.11 with `curl-cffi` and `ddgs`.
- **Execution Standards**: Deterministic JSON output across property search, address lookup, school ratings, HOA fees, property taxes, rental estimates, and comp data.
