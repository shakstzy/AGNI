---
name: mercury
site: app.mercury.com
driver: Browser Use CLI 3.0
profile: adithya
---

# Mercury Banking Dashboard Browser Adapter

## Purpose
Mercury startup business banking, checking, treasury accounts, and virtual corporate debit cards.

## Automation Standard
Automated through Browser Use CLI 3.0 via dedicated Chrome CDP port isolation:
```bash
./.agents/skills/browser/cli/browser opencli --site app.mercury.com --profile adithya --url https://app.mercury.com/cards
```

## Key Capabilities & Workflows
- **Navigation**: Direct deep-linking via sitemap routes (`SITE.md`).
- **Virtual Card Issuance**: Automated issuance of $5 monthly capped virtual debit cards for service signups (`workflows/create-virtual-card.md`).
- **Inspection**: Semantic element anchors and accessibility roles (`sitemap.json` and `pages/`).
- **Profile Persistence**: Stateful Chrome session stored under `/home/shakstzy/HADES/.agents/skills/browser/sitemaps/app.mercury.com/profiles/adithya/user_data`.

## Boundaries & Human Intervention
- Stop immediately on CAPTCHA, SMS/Email OTP checkpoints, or biometric / passkey prompts.
- Never log, export, or leak Bitwarden secrets or session cookies into chat or transcripts.
- Never initiate wire transfers, ACH transfers, or card deletions.
- Never print full 16-digit card numbers (PAN) or security codes (CVV); only record nickname and `last4`.
