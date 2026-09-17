---
site: firecrawl.dev
login_required: true
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# Firecrawl Sitemap

## Overview
Firecrawl web scraping and markdown extraction API console, crawler jobs, and credit metrics via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site firecrawl.dev --profile adithya --url https://www.firecrawl.dev/app
```

## Top-Level Routes
- `/app` -> `pages/dashboard.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Verify Scrape Job & Credits -> `workflows/verify-scrape-job.md`

## Human Boundaries
Do not bypass security challenges, email PIN checkpoints, payment steps, or phone verification without notifying the operator.
