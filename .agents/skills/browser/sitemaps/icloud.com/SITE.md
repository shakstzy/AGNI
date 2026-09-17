---
site: icloud.com
login_required: true
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# iCloud & iCloud Mail Sitemap

## Overview
Apple iCloud web suite for iCloud Mail, Notes, Reminders, Calendar, and Find My via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site icloud.com --profile adithya --url https://www.icloud.com/mail/
```

## Top-Level Routes
- `/mail/` -> `pages/mail.md`
- `/` -> `pages/launchpad.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Check iCloud Mail Inbox -> `workflows/read-inbox.md`

## Human Boundaries
Do not bypass security challenges, email PIN checkpoints, payment steps, or phone verification without notifying the operator.
