---
site: youtube.com
login_required: false
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# YouTube Sitemap

## Overview
YouTube video platform for searching video essays, channel inspection, and Shorts monitoring via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site youtube.com --profile adithya --url https://www.youtube.com/
```

## Top-Level Routes
- `/` -> `pages/home.md`
- `/@<handle>/shorts` -> `pages/channel_shorts.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Inspect Channel Videos -> `workflows/channel-inspection.md`

## Human Boundaries
Do not bypass security challenges, email PIN checkpoints, payment steps, or phone verification without notifying the operator.
