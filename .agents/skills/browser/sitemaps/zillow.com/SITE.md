---
site: zillow.com
login_required: true
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# Zillow Rental Manager Sitemap

## Overview
Zillow Rental Manager for landlord listings, tenant applications, leads, and lease messaging via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site zillow.com --profile adithya --url https://www.zillow.com/rental-manager/inbox
```

## Top-Level Routes
- `/rental-manager/inbox` -> `pages/inbox.md`
- `/rental-manager/properties` -> `pages/properties.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Inspect Rental Leads & Messages -> `workflows/check-leads.md`

## Human Boundaries
Do not bypass security challenges, email PIN checkpoints, payment steps, or phone verification without notifying the operator.
