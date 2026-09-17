---
name: studio
site: studio.youtube.com
driver: Browser Use CLI 3.0
profile: adithya
---

# YouTube Studio Browser Adapter

## Purpose
YouTube Studio creator dashboard for Shorts uploading, video metadata, and channel analytics.

## Automation Standard
Automated through Browser Use CLI 3.0 via dedicated Chrome CDP port isolation:
```bash
./.agents/skills/browser/cli/browser opencli --site studio.youtube.com --profile adithya --url https://studio.youtube.com/
```

## Key Capabilities & Workflows
- **Navigation**: Direct deep-linking via sitemap routes (`SITE.md`).
- **Inspection**: Semantic element anchors and accessibility roles (`sitemap.json` and `pages/`).
- **Profile Persistence**: Stateful Chrome session stored under `/home/shakstzy/HADES/.agents/skills/browser/sitemaps/studio.youtube.com/profiles/adithya/user_data`.

## Boundaries & Human Intervention
- Stop immediately on CAPTCHA, SMS/Email OTP checkpoints, or biometric / passkey prompts.
- Never log, export, or leak Bitwarden secrets or session cookies into chat or transcripts.
- Stop before unauthorized state mutations, payments, or destructive account modifications.
