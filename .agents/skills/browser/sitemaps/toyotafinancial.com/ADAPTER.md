---
name: toyota-financial
site: toyotafinancial.com
driver: Browser Use CLI 3.0
profile: adithya
---

# Toyota Financial Services Browser Adapter

## Purpose
Toyota Financial vehicle financing, auto lease and loan details, payment schedules, and payoff quotes.

## Automation Standard
Automated through Browser Use CLI 3.0 via dedicated Chrome CDP port isolation:
```bash
./.agents/skills/browser/cli/browser opencli --site toyotafinancial.com --profile adithya --url https://www.toyotafinancial.com/us/en/login.html
```

## Key Capabilities & Workflows
- **Navigation**: Direct deep-linking via sitemap routes (`SITE.md`).
- **Inspection**: Semantic element anchors and accessibility roles (`sitemap.json` and `pages/`).
- **Profile Persistence**: Stateful Chrome session stored under `/home/shakstzy/HADES/.agents/skills/browser/sitemaps/toyotafinancial.com/profiles/adithya/user_data`.

## Boundaries & Human Intervention
- Stop immediately on CAPTCHA, SMS/Email OTP checkpoints, or biometric / passkey prompts.
- Never log, export, or leak Bitwarden secrets or session cookies into chat or transcripts.
- Halt immediately if security questions or one-time verification codes appear. Do not submit payments.
