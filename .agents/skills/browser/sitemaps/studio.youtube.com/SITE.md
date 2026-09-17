---
site: studio.youtube.com
login_required: true
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# YouTube Studio Sitemap

## Overview
YouTube Studio creator dashboard for Shorts uploading, video metadata, and channel analytics via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site studio.youtube.com --profile adithya --url https://studio.youtube.com/
```

## Top-Level Routes
- `/` -> `pages/dashboard.md`
- `/channel/*/videos` -> `pages/content.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Check Video & Short Status -> `workflows/check-content-status.md`

## Human Boundaries
Do not bypass security challenges, email PIN checkpoints, payment steps, or phone verification without notifying the operator.
