# Apify Local Skill Adapter Specification

Technical contract for Apify REST integration and pluggable adapters.

## Core Contract

- Binary / Script: `.agents/skills/local/apify/apify.py`
- System Path: Symlinked to `~/.local/bin/apify`
- Primary Dependency: Python 3 standard library (`urllib.request`, `json`, `subprocess`, `argparse`)

## Pluggable Adapters

### `adapters/people_search.py`
- **Primary Actor**: `jungle_synthesizer/truepeoplesearch-people-search-scraper` (Actor ID: `UYTT0xbGOrNPkEBcH`)
- **Fallback Actor**: `apivault_labs/skip-trace-people-finder` (Actor ID: `gSv8lJykdzOrYycAq`)
- **Query Modes**:
  - `phone`: 10-digit reverse telephone lookup
  - `name`: First and last name search with optional city/state filters
  - `address`: Street address reverse property search
- **Output Schema**:
  - `full_name`: string
  - `age`: integer or null
  - `phones`: list of phone strings with line type and carrier metadata
  - `emails`: list of email addresses
  - `current_address`: string
  - `past_addresses`: list of strings
  - `relatives`: list of name/age strings
  - `associates`: list of name/age strings
  - `profile_url`: string
  - `source`: string
