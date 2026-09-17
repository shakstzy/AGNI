---
site: autods.com
login_required: true
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# AutoDS Sitemap

## Overview
AutoDS dropshipping automation platform for product import, pricing rules, and auto-ordering via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site autods.com --profile adithya --url https://platform.autods.com/dashboard
```

## Top-Level Routes
- `/dashboard` -> `pages/dashboard.md`
- `/products` -> `pages/products.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Check AutoDS Sync Status -> `workflows/check-orders.md`

## Human Boundaries
Do not bypass security challenges, email PIN checkpoints, payment steps, or phone verification without notifying the operator.
