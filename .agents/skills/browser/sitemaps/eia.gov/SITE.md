---
site: eia.gov
login_required: false
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# EIA Sitemap

## Overview
U.S. Energy Information Administration Open Data API registration, documentation, and wholesale electricity and grid data access via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site eia.gov --profile adithya --url https://www.eia.gov/opendata/register.php
```

## Top-Level Routes
- `/opendata/register.php` -> `pages/register.md`
- `/developer` -> `pages/developer.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Register & Retrieve Free API Key -> `workflows/request-api-key.md`

## Human Boundaries
Do not bypass security challenges or bot detection without notifying the operator.
