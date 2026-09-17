---
site: tinder.com
login_required: true
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# Tinder Sitemap

## Overview
Tinder web dating portal for recommendation browsing, profile discovery, and match conversations via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site tinder.com --profile adithya --url https://tinder.com/app/recs
```

## Top-Level Routes
- `/app/recs` -> `pages/recs.md`
- `/app/messages` -> `pages/messages.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- List Matches & Unread Messages -> `workflows/inspect-matches.md`

## Human Boundaries
Do not bypass security challenges, email PIN checkpoints, payment steps, or phone verification without notifying the operator.
