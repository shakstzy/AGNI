---
name: instantusername
site: instantusername.com
driver: Browser Use CLI 3.0
profile: adithya
---

# Instant Username Browser Adapter

## Purpose
Instant Username search engine checking handle availability across 100+ social platforms.

## Automation Standard
Automated through Browser Use CLI 3.0 via dedicated Chrome CDP port isolation:
```bash
./.agents/skills/browser/cli/browser opencli --site instantusername.com --profile adithya --url https://instantusername.com/
```

## Key Capabilities & Workflows
- **Navigation**: Direct deep-linking via sitemap routes (`SITE.md`).
- **Inspection**: Semantic element anchors and accessibility roles (`sitemap.json` and `pages/`).
- **Profile Persistence**: Stateful Chrome session stored under `/home/shakstzy/HADES/.agents/skills/browser/sitemaps/instantusername.com/profiles/adithya/user_data`.

## Boundaries & Human Intervention
- Stop immediately on CAPTCHA, SMS/Email OTP checkpoints, or biometric / passkey prompts.
- Never log, export, or leak Bitwarden secrets or session cookies into chat or transcripts.
- Stop before unauthorized state mutations, payments, or destructive account modifications.
