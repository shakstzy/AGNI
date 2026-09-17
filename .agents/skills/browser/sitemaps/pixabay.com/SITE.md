---
site: pixabay.com
login_required: false
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# Pixabay Sitemap

## Overview
Pixabay royalty-free stock imagery, vector graphics, illustration, and footage search via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site pixabay.com --profile adithya --url https://pixabay.com/
```

## Top-Level Routes
- `/` -> `pages/home.md`
- `/images/search/<query>/` -> `pages/search_results.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Search Royalty-Free Media -> `workflows/search-assets.md`

## Human Boundaries
Do not bypass security challenges, email PIN checkpoints, payment steps, or phone verification without notifying the operator.
