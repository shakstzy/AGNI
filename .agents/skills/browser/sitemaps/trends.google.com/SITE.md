---
site: trends.google.com
login_required: false
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# Google Trends Sitemap

## Overview
Google Trends search interest analysis, regional breakdown, related queries, and daily trending searches via Browser Use CLI 3.0.

## Tier 1 Deterministic CLI
For direct programmatic analytics without headless browser overhead, use the native CLI (`google-trends` / `trends`):
```bash
google-trends trending --geo US
google-trends explore "keyword" --time 3m
google-trends velocity "keyword"
google-trends breakout --query "topic"
```
See `.agents/skills/local/google-trends/GUIDE.md`.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site trends.google.com --profile adithya --url https://trends.google.com/trends/trendingnow?geo=US
```

## Top-Level Routes
- `/trends/trendingnow?geo=US` -> `pages/trending_now.md`
- `/trends/explore` -> `pages/explore.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Analyze Search Term Interest Over Time -> `workflows/explore-query.md`

## Human Boundaries
Do not bypass security challenges, email PIN checkpoints, payment steps, or phone verification without notifying the operator.
