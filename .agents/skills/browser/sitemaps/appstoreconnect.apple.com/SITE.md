---
site: appstoreconnect.apple.com
login_required: true
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# App Store Connect

## Overview
Automated inspection of App Store Connect builds, TestFlight statuses, bundle identifiers, and developer integrations.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --profile adithya --url https://appstoreconnect.apple.com/apps
```

## Top-Level Routes
- `/apps` -> `pages/apps.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Review TestFlight Build Status -> `workflows/review.md`

## Human Boundaries
Stop for Apple passkey/device authentication that cannot be completed automatically, Apple Developer Program legal agreements, paid renewals, and production store submissions.
