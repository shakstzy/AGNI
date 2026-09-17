---
site: instagram.com
login_required: true
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# Instagram Sitemap

## Overview
Instagram visual network for creator profiles, reels, direct message inquiries, and media posts via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site instagram.com --profile adithya --url https://www.instagram.com/
```

## Top-Level Routes
- `/` -> `pages/feed.md`
- `/<username>/` -> `pages/profile.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Check Profile Status & Follower Metrics -> `workflows/profile-check.md`

## Human Boundaries
Do not bypass security challenges, email PIN checkpoints, payment steps, or phone verification without notifying the operator.
