---
site: dashboard.plaid.com
login_required: true
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# Plaid Developer Dashboard Sitemap

## Overview
Plaid developer portal for financial API keys, item connection health, logs, and sandbox testing via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site dashboard.plaid.com --profile adithya --url https://dashboard.plaid.com/signin
```

## Top-Level Routes
- `/signin` -> `pages/signin.md`
- `/overview` -> `pages/overview.md`
- `/team/keys` -> `pages/team_keys.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Check Plaid API Usage and Connected Items -> `workflows/check-api-status.md`

## Human Boundaries
Never reveal or copy production API secrets into unencrypted outputs. Stop on 2FA authentication checkpoints.
