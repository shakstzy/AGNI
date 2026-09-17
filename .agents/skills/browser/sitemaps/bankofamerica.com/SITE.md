---
site: bankofamerica.com
login_required: true
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# Bank of America Online Banking Sitemap

## Overview
Bank of America consumer banking, savings, checking, and credit card account management via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site bankofamerica.com --profile adithya --url https://www.bankofamerica.com
```

## Top-Level Routes
- `/login/sign-in/signOnV2Screen.go` -> `pages/signon.md`
- `/myaccounts/brain/redirect.go` -> `pages/accounts.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Check Bank of America Account Summary -> `workflows/check-accounts.md`

## Human Boundaries
Halt immediately on mobile authorization pushes or security question prompts. Never initiate outgoing transfers or Zelle transactions.
