---
site: card.apple.com
login_required: true
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# Apple Card Portal Sitemap

## Overview
Apple Card web portal for monthly statements, Daily Cash tracking, and payment history via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site card.apple.com --profile adithya --url https://card.apple.com
```

## Top-Level Routes
- `/` -> `pages/landing.md`
- `/statements` -> `pages/statements.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Inspect Apple Card Balance and Statements -> `workflows/check-card-balance.md`

## Human Boundaries
Stop on Apple ID two-factor authentication or device PIN prompts. Never submit payment requests without explicit human instruction.
