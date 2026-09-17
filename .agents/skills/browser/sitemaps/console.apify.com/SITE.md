---
site: console.apify.com
login_required: true
driver: Browser Use CLI 3.0
profile_hint: apify
---

# Apify Console Sitemap

## Overview
Apify web scraping, actors, dataset runs, proxy management, and API token console via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site console.apify.com --profile apify --url https://console.apify.com
```

## Top-Level Routes
- `/actors` -> `pages/actors.md`
- Profiles -> `profiles/REGISTRY.md`

## Human Boundaries
Do not bypass security challenges, email PIN checkpoints, payment steps, or phone verification without notifying the operator.
