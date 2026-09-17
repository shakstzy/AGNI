---
name: trends
site: trends.google.com
driver: Browser Use CLI 3.0
profile: adithya
---

# Google Trends Browser Adapter

## Purpose
Google Trends search interest analysis, regional breakdown, related queries, and daily trending searches.

## Deterministic Execution Standard
- **Tier 1 (Primary, <1s)**: Run `google-trends` CLI (`.agents/skills/local/google-trends/GUIDE.md`) for velocity metrics, interest over time, daily trending searches, and breakout tracking.
- **Tier 2 (Interactive/DOM UI)**: Automated through Browser Use CLI 3.0 via dedicated Chrome CDP port isolation:
```bash
./.agents/skills/browser/cli/browser opencli --site trends.google.com --profile adithya --url https://trends.google.com/trends/trendingnow?geo=US
```

## Key Capabilities & Workflows
- **Navigation**: Direct deep-linking via sitemap routes (`SITE.md`).
- **Inspection**: Semantic element anchors and accessibility roles (`sitemap.json` and `pages/`).
- **Profile Persistence**: Stateful Chrome session stored under `/home/shakstzy/HADES/.agents/skills/browser/sitemaps/trends.google.com/profiles/adithya/user_data`.

## Boundaries & Human Intervention
- Stop immediately on CAPTCHA, SMS/Email OTP checkpoints, or biometric / passkey prompts.
- Never log, export, or leak Bitwarden secrets or session cookies into chat or transcripts.
- Stop before unauthorized state mutations, payments, or destructive account modifications.
