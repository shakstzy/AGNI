---
name: play
site: play.google.com
driver: Browser Use CLI 3.0
profile: adithya
---

# Google Play Console Browser Adapter

## Purpose
Google Play developer console for Android app bundle releases, internal test tracks, and store listings.

## Automation Standard
Automated through Browser Use CLI 3.0 via dedicated Chrome CDP port isolation:
```bash
./.agents/skills/browser/cli/browser opencli --site play.google.com --profile adithya --url https://play.google.com/console/developers
```

## Key Capabilities & Workflows
- **Navigation**: Direct deep-linking via sitemap routes (`SITE.md`).
- **Inspection**: Semantic element anchors and accessibility roles (`sitemap.json` and `pages/`).
- **Profile Persistence**: Stateful Chrome session stored under `/home/shakstzy/HADES/.agents/skills/browser/sitemaps/play.google.com/profiles/adithya/user_data`.

## Boundaries & Human Intervention
- Stop immediately on CAPTCHA, SMS/Email OTP checkpoints, or biometric / passkey prompts.
- Never log, export, or leak Bitwarden secrets or session cookies into chat or transcripts.
- Stop before unauthorized state mutations, payments, or destructive account modifications.
