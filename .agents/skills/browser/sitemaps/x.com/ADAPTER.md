---
name: x
site: x.com
driver: Browser Use CLI 3.0
profile: adithya
---

# X (formerly Twitter) Browser Adapter

## Purpose
X social network for real-time news, tech announcements, creator feeds, and post monitoring.

## Automation Standard
Automated through Browser Use CLI 3.0 via dedicated Chrome CDP port isolation:
```bash
./.agents/skills/browser/cli/browser opencli --site x.com --profile adithya --url https://x.com/home
```

## Key Capabilities & Workflows
- **Navigation**: Direct deep-linking via sitemap routes (`SITE.md`).
- **Inspection**: Semantic element anchors and accessibility roles (`sitemap.json` and `pages/`).
- **Profile Persistence**: Stateful Chrome session stored under `/home/shakstzy/HADES/.agents/skills/browser/sitemaps/x.com/profiles/adithya/user_data`.

## Boundaries & Human Intervention
- Stop immediately on CAPTCHA, SMS/Email OTP checkpoints, or biometric / passkey prompts.
- Never log, export, or leak Bitwarden secrets or session cookies into chat or transcripts.
- Stop before unauthorized state mutations, payments, or destructive account modifications.
