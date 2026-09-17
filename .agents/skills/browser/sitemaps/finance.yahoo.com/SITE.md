---
site: finance.yahoo.com
login_required: false
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# Yahoo Finance Sitemap

## Overview
Yahoo Finance market quotes, portfolio tracking, watchlist monitoring, stock financials, and market news via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site finance.yahoo.com --profile adithya --url https://finance.yahoo.com/
```

## Top-Level Routes
- `/` -> `pages/home.md`
- `/portfolios` -> `pages/portfolios.md`
- `/quote/*` -> `pages/quote.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Check Watchlist Quotes and Market Indices -> `workflows/check-watchlist.md`

## Human Boundaries
Halt on Yahoo login security checkpoints. Do not link external broker accounts or perform external mutations.
