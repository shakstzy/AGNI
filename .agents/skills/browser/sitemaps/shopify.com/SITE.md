---
site: shopify.com
login_required: true
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# Shopify Admin Sitemap

## Overview
Shopify merchant admin panel for store settings, products, apps, and order fulfillment via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site shopify.com --profile adithya --url https://admin.shopify.com/
```

## Top-Level Routes
- `/` -> `pages/dashboard.md`
- `/products` -> `pages/products.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Catalog & App Consent -> `workflows/catalog-sync.md`

## Human Boundaries
Do not bypass security challenges, email PIN checkpoints, payment steps, or phone verification without notifying the operator.
