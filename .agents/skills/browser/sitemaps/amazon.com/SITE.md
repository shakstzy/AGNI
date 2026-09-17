---
site: amazon.com
login_required: false
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# Amazon Sitemap

## Overview
Amazon marketplace search, product details, and competitor pricing research via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site amazon.com --profile adithya --url https://www.amazon.com/
```

## Top-Level Routes
- `/s?k=<query>` -> `pages/search.md`
- `/dp/<ASIN>` -> `pages/product.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Product Research -> `workflows/product-research.md`

## Human Boundaries
Do not bypass security challenges, email PIN checkpoints, payment steps, or phone verification without notifying the operator.
