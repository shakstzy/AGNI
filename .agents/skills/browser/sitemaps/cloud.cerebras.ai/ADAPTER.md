---
name: cloud
site: cloud.cerebras.ai
driver: Browser Use CLI 3.0
profile: adithya
---

# Cerebras Cloud Browser Adapter

## Purpose
Cerebras Cloud ultra-fast wafer-scale inference engine, playground, and API key management.

## Automation Standard
Automated through Browser Use CLI 3.0 via dedicated Chrome CDP port isolation:
```bash
./.agents/skills/browser/cli/browser opencli --site cloud.cerebras.ai --profile adithya --url https://cloud.cerebras.ai/platform
```

## Key Capabilities & Workflows
- **Navigation**: Direct deep-linking via sitemap routes (`SITE.md`).
- **Inspection**: Semantic element anchors and accessibility roles (`sitemap.json` and `pages/`).
- **Profile Persistence**: Stateful Chrome session stored under `/home/shakstzy/HADES/.agents/skills/browser/sitemaps/cloud.cerebras.ai/profiles/adithya/user_data`.

## Boundaries & Human Intervention
- Stop immediately on CAPTCHA, SMS/Email OTP checkpoints, or biometric / passkey prompts.
- Never log, export, or leak Bitwarden secrets or session cookies into chat or transcripts.
- Stop before unauthorized state mutations, payments, or destructive account modifications.
