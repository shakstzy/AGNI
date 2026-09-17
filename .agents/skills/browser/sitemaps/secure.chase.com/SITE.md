---
site: secure.chase.com
login_required: true
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# Chase Online Banking Sitemap

## Overview
Chase consumer and business banking, credit cards, account balances, and transaction history via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site secure.chase.com --profile adithya --url https://secure.chase.com/web/auth/#/logon/logon/chaseOnline
```

## Top-Level Routes
- `/web/auth/#/logon/logon/chaseOnline` -> `pages/logon.md`
- `/web/auth/#/dashboard/overview` -> `pages/dashboard.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Check Chase Account Balances -> `workflows/check-accounts.md`

## Human Boundaries
Do not attempt money transfers, wire orders, bill payments, or MFA bypass without explicit operator confirmation.
