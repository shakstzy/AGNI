---
site: dashboard.stripe.com
login_required: true
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# Stripe Dashboard Sitemap

## Overview
Stripe payments processing console, gross sales volume, charges, customers, and payout tracking via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site dashboard.stripe.com --profile adithya --url https://dashboard.stripe.com/login
```

## Top-Level Routes
- `/login` -> `pages/login.md`
- `/` -> `pages/home.md`
- `/payments` -> `pages/payments.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Monitor Stripe Revenue and Payout Schedule -> `workflows/check-gross-volume.md`

## Human Boundaries
Stop on hardware FIDO2 keys or authenticator app prompts. Never issue refunds, initiate payouts, or mutate API keys without direct authorization.
