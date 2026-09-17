---
name: apple-card
site: card.apple.com
driver: Browser Use CLI 3.0
profile: adithya
---

# Apple Card Portal Browser Adapter

## Purpose
Apple Card web portal for monthly statements, Daily Cash tracking, and payment history.

## Automation Standard
Automated through Browser Use CLI 3.0 via dedicated Chrome CDP port isolation:
```bash
./.agents/skills/browser/cli/browser opencli --site card.apple.com --profile adithya --url https://card.apple.com
```

## Key Capabilities & Workflows
- **Navigation**: Direct deep-linking via sitemap routes (`SITE.md`).
- **Inspection**: Semantic element anchors and accessibility roles (`sitemap.json` and `pages/`).
- **Profile Persistence**: Stateful Chrome session stored under `/home/shakstzy/HADES/.agents/skills/browser/sitemaps/card.apple.com/profiles/adithya/user_data`.

## Boundaries & Human Intervention
- Stop immediately on CAPTCHA, SMS/Email OTP checkpoints, or biometric / passkey prompts.
- Never log, export, or leak Bitwarden secrets or session cookies into chat or transcripts.
- Stop on Apple ID two-factor authentication or device PIN prompts. Never submit payment requests without explicit human instruction.
