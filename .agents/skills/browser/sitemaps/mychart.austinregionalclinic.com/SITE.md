---
site: mychart.austinregionalclinic.com
login_required: true
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# ARC MyChart Sitemap

## Overview
Austin Regional Clinic MyChart portal for appointments, test results, doctor messaging, and bills via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site mychart.austinregionalclinic.com --profile adithya --url https://mychart.austinregionalclinic.com/MyChart/Home/
```

## Top-Level Routes
- `/MyChart/Authentication/Login` -> `pages/login.md`
- `/MyChart/Home/` -> `pages/home.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Check Lab Results & Appointments -> `workflows/health-check.md`

## Human Boundaries
Do not bypass security challenges, email PIN checkpoints, payment steps, or phone verification without notifying the operator.
