---
site: app.mercury.com
login_required: true
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# Mercury Banking Dashboard Sitemap

## Overview
Mercury startup business banking, checking, treasury accounts, and virtual corporate debit cards via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site app.mercury.com --profile adithya --url https://app.mercury.com/dashboard
```

## Top-Level Routes
- `/login` -> `pages/login.md`
- `/dashboard` -> `pages/dashboard.md`
- `/cards` -> `pages/cards.md`
- `/issue-card` -> `pages/issue-card.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Check Account Balance -> `workflows/check-balance.md`
- View Cards -> `workflows/view-cards.md`
- Create Virtual Card -> `workflows/create-virtual-card.md`

## Human Boundaries
Stop on login, TOTP, SMS verification, or biometric challenge. Never initiate wire or ACH transfers. Never print full card PAN or CVV.
