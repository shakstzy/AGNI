---
site: secure.cmghomeloans.com
login_required: true
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# CMG Home Loans Portal Sitemap

## Overview
CMG Home Loans web portal for mortgage loan servicing, balance queries, escrow tracking, and 1098 tax document access via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site secure.cmghomeloans.com --profile adithya --url https://secure.cmghomeloans.com/
```

## Top-Level Routes
- `/` -> `pages/login.md`
- `/dashboard` -> `pages/dashboard.md`
- `/statements` -> `pages/statements.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Inspect Mortgage Balance & Escrow -> `workflows/check-mortgage-balance.md`

## Human Boundaries
Stop on two-factor SMS/email OTP challenges or security questions. Never submit payment authorizations without explicit user approval.
