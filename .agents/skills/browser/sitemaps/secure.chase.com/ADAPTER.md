---
name: chase
site: secure.chase.com
driver: Browser Use CLI 3.0
profile: adithya
---

# Chase Online Banking Browser Adapter

## Purpose
Chase consumer and business banking, credit cards, account balances, and transaction history.

## Automation Standard
Automated through Browser Use CLI 3.0 via dedicated Chrome CDP port isolation:
```bash
./.agents/skills/browser/cli/browser opencli --site secure.chase.com --profile adithya --url https://secure.chase.com/web/auth/#/logon/logon/chaseOnline
```

## Key Capabilities & Workflows
- **Navigation**: Direct deep-linking via sitemap routes (`SITE.md`).
- **Inspection**: Semantic element anchors and accessibility roles (`sitemap.json` and `pages/`).
- **Profile Persistence**: Stateful Chrome session stored under `/home/shakstzy/HADES/.agents/skills/browser/sitemaps/secure.chase.com/profiles/adithya/user_data`.

## Boundaries & Human Intervention
- Stop immediately on CAPTCHA, SMS/Email OTP checkpoints, or biometric / passkey prompts.
- Never log, export, or leak Bitwarden secrets or session cookies into chat or transcripts.
- Do not attempt money transfers, wire orders, bill payments, or MFA bypass without explicit operator confirmation.
