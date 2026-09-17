---
site: fitbit.com
login_required: true
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# Fitbit Web Sitemap

## Overview
Fitbit web dashboard for health metrics, daily steps, sleep tracking, and device battery status via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site fitbit.com --profile adithya --url https://www.fitbit.com/login
```

## Top-Level Routes
- `/dashboard` -> `pages/dashboard.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Inspect Daily Health Metrics -> `workflows/health-metrics.md`

## Human Boundaries
Do not bypass security challenges, email PIN checkpoints, payment steps, or phone verification without notifying the operator.
