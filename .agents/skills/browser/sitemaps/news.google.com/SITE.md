---
site: news.google.com
login_required: false
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# Google News Sitemap

## Overview
Google News aggregator for top headlines, industry coverage, and real-time event monitoring via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site news.google.com --profile adithya --url https://news.google.com/home
```

## Top-Level Routes
- `/home` -> `pages/home.md`
- `/search?q=<query>` -> `pages/search.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Monitor Industry News Headlines -> `workflows/topic-monitoring.md`

## Human Boundaries
Do not bypass security challenges, email PIN checkpoints, payment steps, or phone verification without notifying the operator.
