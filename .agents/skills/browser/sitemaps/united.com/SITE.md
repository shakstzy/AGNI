---
site: united.com
login_required: true
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# United Airlines Sitemap

## Overview
United Airlines flight booking, reservations, MileagePlus account, and flight status via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site united.com --profile adithya --url https://www.united.com/en/us
```

## Top-Level Routes
- `/en/us` -> `pages/home.md`
- `/en/us/flight-search/book-a-flight/results` -> `pages/flight_results.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Search United Flights -> `workflows/flight-lookup.md`

## Human Boundaries
Do not bypass security challenges, email PIN checkpoints, payment steps, or phone verification without notifying the operator.
