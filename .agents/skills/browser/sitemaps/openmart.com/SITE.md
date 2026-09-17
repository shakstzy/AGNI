---
site: openmart.com
login_required: true
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# Openmart Sitemap

## Overview
Openmart public web portal and app redirection via Browser Use CLI 3.0. For authenticated B2B searches, see `app.openmart.com/`.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site openmart.com --profile adithya --url https://www.openmart.com/
```

## Top-Level Routes
- `/` -> `pages/landing.md`
- `/pricing` -> `pages/pricing.md`
- Dashboard App -> `sitemaps/app.openmart.com/`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Redirect to Openmart Dashboard App -> `workflows/navigate-to-app.md`

## Human Boundaries
Stop on login challenges, credit card entry, or CAPTCHA.
