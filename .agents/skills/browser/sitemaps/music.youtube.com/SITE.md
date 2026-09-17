---
site: music.youtube.com
login_required: true
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# YouTube Music Sitemap

## Overview
YouTube Music streaming web player for playlist playback, library tracks, and audio streaming via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site music.youtube.com --profile adithya --url https://music.youtube.com/
```

## Top-Level Routes
- `/` -> `pages/home.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Control Music Playback -> `workflows/play-track.md`

## Human Boundaries
Do not bypass security challenges, email PIN checkpoints, payment steps, or phone verification without notifying the operator.
