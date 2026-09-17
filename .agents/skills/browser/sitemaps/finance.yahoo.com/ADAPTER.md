---
name: yahoo-finance
site: finance.yahoo.com
driver: Browser Use CLI 3.0
profile: adithya
---

# Yahoo Finance Browser Adapter

## Purpose
Yahoo Finance market quotes, portfolio tracking, watchlist monitoring, stock financials, and market news.

## Automation Standard
Automated through Browser Use CLI 3.0 via dedicated Chrome CDP port isolation:
```bash
./.agents/skills/browser/cli/browser opencli --site finance.yahoo.com --profile adithya --url https://finance.yahoo.com/
```

## Key Capabilities & Workflows
- **Navigation**: Direct deep-linking via sitemap routes (`SITE.md`).
- **Inspection**: Semantic element anchors and accessibility roles (`sitemap.json` and `pages/`).
- **Profile Persistence**: Stateful Chrome session stored under `/home/shakstzy/HADES/.agents/skills/browser/sitemaps/finance.yahoo.com/profiles/adithya/user_data`.

## Boundaries & Human Intervention
- Stop immediately on CAPTCHA, SMS/Email OTP checkpoints, or biometric / passkey prompts.
- Never log, export, or leak Bitwarden secrets or session cookies into chat or transcripts.
- Halt on Yahoo login security checkpoints. Do not link external broker accounts or perform external mutations.
