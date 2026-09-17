---
site: developer.apple.com
login_required: true
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# Apple Developer Sitemap

## Overview
Apple Developer portal for certificates, identifiers, provisioning profiles, and documentation via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site developer.apple.com --profile adithya --url https://developer.apple.com/account/
```

## Top-Level Routes
- `/account/` -> `pages/account.md`
- `/account/resources/certificates/list` -> `pages/certificates.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Check Developer Account Resources -> `workflows/check-membership.md`

## Human Boundaries
Do not bypass security challenges, email PIN checkpoints, payment steps, or phone verification without notifying the operator.
