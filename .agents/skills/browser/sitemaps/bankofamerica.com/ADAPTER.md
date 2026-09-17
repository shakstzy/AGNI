---
name: bank-of-america
site: bankofamerica.com
driver: Browser Use CLI 3.0
profile: adithya
---

# Bank of America Online Banking Browser Adapter

## Purpose
Bank of America consumer banking, savings, checking, and credit card account management.

## Automation Standard
Automated through Browser Use CLI 3.0 via dedicated Chrome CDP port isolation:
```bash
./.agents/skills/browser/cli/browser opencli --site bankofamerica.com --profile adithya --url https://www.bankofamerica.com
```

## Key Capabilities & Workflows
- **Navigation**: Direct deep-linking via sitemap routes (`SITE.md`).
- **Inspection**: Semantic element anchors and accessibility roles (`sitemap.json` and `pages/`).
- **Profile Persistence**: Stateful Chrome session stored under `/home/shakstzy/HADES/.agents/skills/browser/sitemaps/bankofamerica.com/profiles/adithya/user_data`.

## Boundaries & Human Intervention
- Stop immediately on CAPTCHA, SMS/Email OTP checkpoints, or biometric / passkey prompts.
- Never log, export, or leak Bitwarden secrets or session cookies into chat or transcripts.
- Halt immediately on mobile authorization pushes or security question prompts. Never initiate outgoing transfers or Zelle transactions.
