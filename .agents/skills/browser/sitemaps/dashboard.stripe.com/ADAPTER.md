---
name: stripe
site: dashboard.stripe.com
driver: Browser Use CLI 3.0
profile: adithya
---

# Stripe Dashboard Browser Adapter

## Purpose
Stripe payments processing console, gross sales volume, charges, customers, and payout tracking.

## Automation Standard
Automated through Browser Use CLI 3.0 via dedicated Chrome CDP port isolation:
```bash
./.agents/skills/browser/cli/browser opencli --site dashboard.stripe.com --profile adithya --url https://dashboard.stripe.com/login
```

## Key Capabilities & Workflows
- **Navigation**: Direct deep-linking via sitemap routes (`SITE.md`).
- **Inspection**: Semantic element anchors and accessibility roles (`sitemap.json` and `pages/`).
- **Profile Persistence**: Stateful Chrome session stored under `/home/shakstzy/HADES/.agents/skills/browser/sitemaps/dashboard.stripe.com/profiles/adithya/user_data`.

## Boundaries & Human Intervention
- Stop immediately on CAPTCHA, SMS/Email OTP checkpoints, or biometric / passkey prompts.
- Never log, export, or leak Bitwarden secrets or session cookies into chat or transcripts.
- Stop on hardware FIDO2 keys or authenticator app prompts. Never issue refunds, initiate payouts, or mutate API keys without direct authorization.
