---
site: americanexpress.com
login_required: true
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# American Express Account Portal Sitemap

## Overview
American Express credit card management, statement balances, transactions, and Membership Rewards via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site americanexpress.com --profile adithya --url https://www.americanexpress.com/en-us/account/login
```

## Top-Level Routes
- `/en-us/account/login` -> `pages/login.md`
- `/dashboard` -> `pages/dashboard.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Check Amex Statement Balance and Rewards -> `workflows/check-balance.md`

## Human Boundaries
Stop on card verification codes or two-factor SMS prompts. Never authorize payments or credit line changes.
