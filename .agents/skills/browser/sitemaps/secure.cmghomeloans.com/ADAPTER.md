---
name: cmg-home-loans
site: secure.cmghomeloans.com
driver: Browser Use CLI 3.0
profile: adithya
---

# CMG Home Loans Browser Adapter

## Purpose
CMG Home Loans borrower portal for mortgage loan servicing, unpaid principal balance, interest rate, escrow balance, monthly payment breakdown (P&I, taxes, insurance), and 1098 year-end tax statements.

## Automation Standard
Automated through Browser Use CLI 3.0 via dedicated Chrome CDP port isolation:
```bash
./.agents/skills/browser/cli/browser opencli --site secure.cmghomeloans.com --profile adithya --url https://secure.cmghomeloans.com/
```

## Key Capabilities & Workflows
- **Navigation**: Direct deep-linking via sitemap routes (`SITE.md`).
- **Inspection**: Semantic element anchors and accessibility roles (`sitemap.json` and `pages/`).
- **Profile Persistence**: Stateful Chrome session stored under `/home/shakstzy/HADES/.agents/skills/browser/sitemaps/secure.cmghomeloans.com/profiles/adithya/user_data`.

## Boundaries & Human Intervention
- Stop immediately on CAPTCHA, SMS/Email OTP checkpoints, or biometric / passkey prompts.
- Never log, export, or leak Bitwarden secrets or session cookies into chat or transcripts.
- Halt immediately if security questions or one-time verification codes appear.
- Never initiate or modify payments or autopay schedules without explicit user confirmation.
