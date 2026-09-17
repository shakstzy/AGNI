---
site: adsmanager.facebook.com
login_required: true
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# Meta Ads Manager Sitemap

## Overview
Meta Ads Manager for ad campaign monitoring, ad sets, creative assets, and performance spend tracking via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site adsmanager.facebook.com --profile adithya --url https://adsmanager.facebook.com/adsmanager/manage/campaigns
```

## Top-Level Routes
- `/adsmanager/manage/campaigns` -> `pages/campaigns.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Check Campaign Performance & Spend -> `workflows/check-ad-spend.md`

## Human Boundaries
Do not bypass security challenges, email PIN checkpoints, payment steps, or phone verification without notifying the operator.
