---
name: 23andme
site: you.23andme.com
driver: Browser Use CLI 3.0
profile: adithya
---

# 23andMe Browser Adapter

## Purpose
Automate 23andMe customer portal navigation to download raw genetic SNP zip archives and extract health predisposition reports.

## Automation Standard
Automated through Browser Use CLI 3.0 via dedicated Chrome CDP port isolation:
```bash
./.agents/skills/browser/cli/browser opencli --site you.23andme.com --profile adithya --url https://you.23andme.com/tools/data/download/
```

## Key Capabilities & Workflows
- **Navigation**: Direct deep-linking via sitemap routes (`SITE.md`).
- **Inspection**: Semantic element anchors and accessibility roles (`sitemap.json` and `pages/`).
- **Profile Persistence**: Stateful Chrome session stored under `/home/shakstzy/HADES/.agents/skills/browser/sitemaps/you.23andme.com/profiles/adithya/user_data`.

## Boundaries & Human Intervention
- Stop immediately on CAPTCHA, 2FA prompt, or email confirmation code request.
- Never log, export, or leak Bitwarden secrets or session cookies into chat or transcripts.
- Genomic raw data contains sensitive identifiable health information; store downloads strictly in `workspaces/health/state/raw/` or user-specified secure targets.
