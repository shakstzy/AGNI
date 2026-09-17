---
site: x.com
login_required: true
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# X (formerly Twitter) Sitemap

## Overview
X social network for real-time news, tech announcements, creator feeds, and post monitoring via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site x.com --profile adithya --url https://x.com/home
```

## Top-Level Routes
- `/home` -> `pages/home.md`
- `/<username>` -> `pages/profile.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Search Real-Time Posts -> `workflows/search-posts.md`

## Human Boundaries
Do not bypass security challenges, email PIN checkpoints, payment steps, or phone verification without notifying the operator.
