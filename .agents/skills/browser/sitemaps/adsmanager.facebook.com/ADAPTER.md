---
name: adsmanager
site: adsmanager.facebook.com
driver: Browser Use CLI 3.0
profile: adithya
---

# Meta Ads Manager Browser Adapter

## Purpose
Meta Ads Manager for ad campaign monitoring, ad sets, creative assets, and performance spend tracking.

## Automation Standard
Automated through Browser Use CLI 3.0 via dedicated Chrome CDP port isolation:
```bash
./.agents/skills/browser/cli/browser opencli --site adsmanager.facebook.com --profile adithya --url https://adsmanager.facebook.com/adsmanager/manage/campaigns
```

## Key Capabilities & Workflows
- **Navigation**: Direct deep-linking via sitemap routes (`SITE.md`).
- **Inspection**: Semantic element anchors and accessibility roles (`sitemap.json` and `pages/`).
- **Profile Persistence**: Stateful Chrome session stored under `/home/shakstzy/HADES/.agents/skills/browser/sitemaps/adsmanager.facebook.com/profiles/adithya/user_data`.

## Boundaries & Human Intervention
- Stop immediately on CAPTCHA, SMS/Email OTP checkpoints, or biometric / passkey prompts.
- Never log, export, or leak Bitwarden secrets or session cookies into chat or transcripts.
- Stop before unauthorized state mutations, payments, or destructive account modifications.
