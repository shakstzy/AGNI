---
name: plaid
site: dashboard.plaid.com
driver: Browser Use CLI 3.0
profile: adithya
---

# Plaid Developer Dashboard Browser Adapter

## Purpose
Plaid developer portal for financial API keys, item connection health, logs, and sandbox testing.

## Automation Standard
Automated through Browser Use CLI 3.0 via dedicated Chrome CDP port isolation:
```bash
./.agents/skills/browser/cli/browser opencli --site dashboard.plaid.com --profile adithya --url https://dashboard.plaid.com/signin
```

## Key Capabilities & Workflows
- **Navigation**: Direct deep-linking via sitemap routes (`SITE.md`).
- **Inspection**: Semantic element anchors and accessibility roles (`sitemap.json` and `pages/`).
- **Profile Persistence**: Stateful Chrome session stored under `/home/shakstzy/HADES/.agents/skills/browser/sitemaps/dashboard.plaid.com/profiles/adithya/user_data`.

## Boundaries & Human Intervention
- Stop immediately on CAPTCHA, SMS/Email OTP checkpoints, or biometric / passkey prompts.
- Never log, export, or leak Bitwarden secrets or session cookies into chat or transcripts.
- Never reveal or copy production API secrets into unencrypted outputs. Stop on 2FA authentication checkpoints.
