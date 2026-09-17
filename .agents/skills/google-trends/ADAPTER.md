# Google Trends CLI Adapter

Technical adapter contract for Google Trends search interest exploration, query volume velocity calculation, and breakout search detection.

## Operating Contract

- **Binary**: `/home/shakstzy/.local/bin/google-trends` (aliases: `gtrends`, `trends`).
- **Implementation**: `/home/shakstzy/HADES/.agents/skills/local/google-trends/trends.py`.
- **Execution Standards**:
  - Direct native execution (`google-trends <command> [flags]`).
  - Dual-mode architecture:
    - **Tier 1 Fast Stream (<700ms)**: Direct HTTP RSS ingestion for real-time trending queries.
    - **Headless Chrome CDP Engine**: Dedicated port `9305` (profile `adithya`) for deep query exploration, daily time-series extraction, moving averages, and rising breakout terms.
- **Safety**:
  - Non-destructive, read-only analytics.
  - Zero credentials leaked or stored.
  - Rate-limit resilient via browser session persistence in `profiles/adithya/user_data`.
