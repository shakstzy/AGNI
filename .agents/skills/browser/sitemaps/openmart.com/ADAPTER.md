---
name: openmart
site: openmart.com
driver: Browser Use CLI 3.0
profile: adithya
---

# Openmart Browser Adapter

## Purpose
Openmart AI SMB search portal, marketing pages, pricing, and app authentication redirect. Direct dashboard operations are hosted on `app.openmart.com`.

## Automation Standard
Automated through Browser Use CLI 3.0 via dedicated Chrome CDP port isolation:
```bash
./.agents/skills/browser/cli/browser opencli --site openmart.com --profile adithya --url https://www.openmart.com/
```

## Key Capabilities & Workflows
- **Navigation**: Landing page, pricing tier inspection, and session routing to `app.openmart.com`.
- **Inspection**: Semantic element anchors and accessibility roles (`sitemap.json` and `pages/`).
- **Profile Persistence**: Stateful Chrome session stored under `/home/shakstzy/HADES/.agents/skills/browser/sitemaps/openmart.com/profiles/adithya/user_data`.

## Boundaries & Human Intervention
- Stop immediately on CAPTCHA, SMS/Email OTP checkpoints, or payment checkout.
- Never log, export, or leak Bitwarden secrets or session cookies into chat or transcripts.
