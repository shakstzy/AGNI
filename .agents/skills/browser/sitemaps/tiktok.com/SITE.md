---
site: tiktok.com
login_required: true
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# TikTok Sitemap

## Overview
TikTok short-form video platform for creator profile research, video metrics, and Studio uploads via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site tiktok.com --profile adithya --url https://www.tiktok.com/
```

## Top-Level Routes
- `/@<username>` -> `pages/profile.md`
- `/tiktokstudio/upload` -> `pages/studio_upload.md`
- `/signup` -> `pages/signup.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Inspect Creator Profile & Views -> `workflows/creator-research.md`
- Account Registration via Email -> `workflows/signup.md`

## Human Boundaries
Do not bypass security challenges, email PIN checkpoints, payment steps, or phone verification without notifying the operator.
