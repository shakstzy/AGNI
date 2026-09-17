---
name: robinhood
site: robinhood.com
driver: Browser Use CLI 3.0
profile: adithya
---

# Robinhood Investing Browser Adapter

## Purpose
Robinhood brokerage portfolio, stock and crypto holdings, buying power, and order tracking.

## Automation Standard
Automated through Browser Use CLI 3.0 via dedicated Chrome CDP port isolation:
```bash
./.agents/skills/browser/cli/browser opencli --site robinhood.com --profile adithya --url https://robinhood.com
```

## Key Capabilities & Workflows
- **Navigation**: Direct deep-linking via sitemap routes (`SITE.md`).
- **Inspection**: Semantic element anchors and accessibility roles (`sitemap.json` and `pages/`).
- **Profile Persistence**: Stateful Chrome session stored under `/home/shakstzy/HADES/.agents/skills/browser/sitemaps/robinhood.com/profiles/adithya/user_data`.

## Boundaries & Human Intervention
- Stop immediately on CAPTCHA, SMS/Email OTP checkpoints, or biometric / passkey prompts.
- Never log, export, or leak Bitwarden secrets or session cookies into chat or transcripts.
- Stop on mobile push notifications or SMS verification codes. Never execute trades, place orders, or initiate bank transfers.
