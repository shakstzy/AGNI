---
site: cjdropshipping.com
login_required: true
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# CJ Dropshipping Sitemap

## Overview
CJ Dropshipping portal for supplier sourcing, product mapping, and store synchronization via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site cjdropshipping.com --profile adithya --url https://cjdropshipping.com/my-cj.html
```

## Top-Level Routes
- `/my-cj.html` -> `pages/my_cj.md`
- `/list/search.html` -> `pages/product_search.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Store Authorization Verification -> `workflows/store-authorization.md`

## Human Boundaries
Do not bypass security challenges, email PIN checkpoints, payment steps, or phone verification without notifying the operator.
