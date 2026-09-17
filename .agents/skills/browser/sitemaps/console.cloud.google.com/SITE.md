---
site: console.cloud.google.com
login_required: true
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# Google Cloud Console Sitemap

## Overview
Google Cloud Platform console for IAM, Compute Engine, Cloud Run, Storage, and Billing via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site console.cloud.google.com --profile adithya --url https://console.cloud.google.com/home/dashboard
```

## Top-Level Routes
- `/home/dashboard` -> `pages/dashboard.md`
- `/apis/credentials` -> `pages/credentials.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Verify GCP Project Resources -> `workflows/check-resources.md`

## Human Boundaries
Do not bypass security challenges, email PIN checkpoints, payment steps, or phone verification without notifying the operator.
