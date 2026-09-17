---
site: dash.cloudflare.com
login_required: true
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# Cloudflare Dashboard Sitemap

## Overview
Cloudflare dashboard for DNS zone management, Workers & Pages, edge rules, and Zero Trust security via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site dash.cloudflare.com --profile adithya --url https://dash.cloudflare.com/
```

## Top-Level Routes
- `/` -> `pages/home.md`
- `/<account>/<zone>/dns/records` -> `pages/dns.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Verify Zone DNS Records -> `workflows/verify-dns-records.md`

## Human Boundaries
Do not bypass security challenges, email PIN checkpoints, payment steps, or phone verification without notifying the operator.
