---
site: play.google.com
login_required: true
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# Google Play Console Sitemap

## Overview
Google Play developer console for Android app bundle releases, internal test tracks, and store listings via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site play.google.com --profile adithya --url https://play.google.com/console/developers
```

## Top-Level Routes
- `/console/developers` -> `pages/developers.md`
- `/console/developers/*/app/*/tracks/internal-testing` -> `pages/internal_testing.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Check App Release Status & Test Tracks -> `workflows/check-release-status.md`

## Human Boundaries
Do not bypass security challenges, email PIN checkpoints, payment steps, or phone verification without notifying the operator.
