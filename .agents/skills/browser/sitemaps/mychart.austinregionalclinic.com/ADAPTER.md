---
name: mychart
site: mychart.austinregionalclinic.com
driver: Browser Use CLI 3.0
profile: adithya
---

# ARC MyChart Browser Adapter

## Purpose
Austin Regional Clinic MyChart portal for appointments, test results, doctor messaging, and bills.

## Automation Standard
Automated through Browser Use CLI 3.0 via dedicated Chrome CDP port isolation:
```bash
./.agents/skills/browser/cli/browser opencli --site mychart.austinregionalclinic.com --profile adithya --url https://mychart.austinregionalclinic.com/MyChart/Home/
```

## Key Capabilities & Workflows
- **Navigation**: Direct deep-linking via sitemap routes (`SITE.md`).
- **Inspection**: Semantic element anchors and accessibility roles (`sitemap.json` and `pages/`).
- **Profile Persistence**: Stateful Chrome session stored under `/home/shakstzy/HADES/.agents/skills/browser/sitemaps/mychart.austinregionalclinic.com/profiles/adithya/user_data`.

## Boundaries & Human Intervention
- Stop immediately on CAPTCHA, SMS/Email OTP checkpoints, or biometric / passkey prompts.
- Never log, export, or leak Bitwarden secrets or session cookies into chat or transcripts.
- Stop before unauthorized state mutations, payments, or destructive account modifications.
