---
site: bumble.com
login_required: true
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# Bumble Sitemap

## Overview
Bumble web dating portal for Beeline admirers, match queue, conversation replies, and profiles via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site bumble.com --profile adithya --url https://bumble.com/app
```

## Top-Level Routes
- `/app` -> `pages/app.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Inspect Bumble Match Queue -> `workflows/check-match-queue.md`

## Human Boundaries
Do not bypass security challenges, email PIN checkpoints, payment steps, or phone verification without notifying the operator.
