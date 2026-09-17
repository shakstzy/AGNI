---
site: app.alpaca.markets
login_required: true
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# Alpaca Trading Console Sitemap

## Overview
Alpaca web dashboard for managing brokerage paper and live trading accounts, API keys, and order execution.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site app.alpaca.markets --profile adithya --url https://app.alpaca.markets/
```

## Top-Level Routes
- `/` -> Dashboard home (account overview, balance, positions)
- `/paper/dashboard/overview` -> Paper Trading account overview
- `/account/api-keys` -> API key management (generate, view, revoke keys)
- Profiles -> `profiles/REGISTRY.md`

## Human Boundaries
Do not initiate real money deposits or live withdrawals. Paper account resets and paper API key generation are fully authorized.
