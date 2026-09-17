---
name: music
site: music.youtube.com
driver: Browser Use CLI 3.0
profile: adithya
---

# YouTube Music Browser Adapter

## Purpose
YouTube Music streaming web player for playlist playback, library tracks, and audio streaming.

## Automation Standard
Automated through Browser Use CLI 3.0 via dedicated Chrome CDP port isolation:
```bash
./.agents/skills/browser/cli/browser opencli --site music.youtube.com --profile adithya --url https://music.youtube.com/
```

## Key Capabilities & Workflows
- **Navigation**: Direct deep-linking via sitemap routes (`SITE.md`).
- **Inspection**: Semantic element anchors and accessibility roles (`sitemap.json` and `pages/`).
- **Profile Persistence**: Stateful Chrome session stored under `/home/shakstzy/HADES/.agents/skills/browser/sitemaps/music.youtube.com/profiles/adithya/user_data`.

## Boundaries & Human Intervention
- Stop immediately on CAPTCHA, SMS/Email OTP checkpoints, or biometric / passkey prompts.
- Never log, export, or leak Bitwarden secrets or session cookies into chat or transcripts.
- Stop before unauthorized state mutations, payments, or destructive account modifications.
