---
site: aa.com
login_required: true
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# American Airlines Sitemap

## Overview
American Airlines flight booking, reservation management, and AAdvantage loyalty status via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site aa.com --profile adithya --url https://www.aa.com/loyalty/login?from=technicalSupport&locale=en_US
```

## Top-Level Routes
- `/loyalty/login?from=technicalSupport&locale=en_US` -> `pages/login.md`
- `/booking/find-flights` -> `pages/flight_search.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Search Flights -> `workflows/flight-search.md`

## Human Boundaries
Do not bypass security challenges, email PIN checkpoints, payment steps, or phone verification without notifying the operator.
