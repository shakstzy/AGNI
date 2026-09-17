---
site: robinhood.com
login_required: true
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# Robinhood Investing Sitemap

## Overview
Robinhood brokerage portfolio, stock and crypto holdings, buying power, and order tracking via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site robinhood.com --profile adithya --url https://robinhood.com
```

## Top-Level Routes
- `/login` -> `pages/login.md`
- `/` -> `pages/portfolio.md`
- `/crypto` -> `pages/crypto.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Check Robinhood Portfolio Equity and Holdings -> `workflows/check-portfolio.md`

## Human Boundaries
Stop on mobile push notifications or SMS verification codes. Never execute trades, place orders, or initiate bank transfers.
