---
site: myturbotax.intuit.com
login_required: true
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# TurboTax Online Sitemap

## Overview
Intuit TurboTax tax preparation, federal and state return filing status, and archived tax documents via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site myturbotax.intuit.com --profile adithya --url https://myturbotax.intuit.com/
```

## Top-Level Routes
- `/` -> `pages/landing.md`
- `/tax-timeline` -> `pages/timeline.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Check Federal and State Tax Filing Status -> `workflows/check-filing-status.md`

## Human Boundaries
Never alter tax inputs, file returns, or change direct deposit details. Stop on 2FA SMS or email security codes.
