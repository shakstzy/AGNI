---
site: app.clay.com
login_required: true
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# Clay Sitemap

## Overview
Clay data enrichment platform combining multiple providers for automated outbound CRM workflows via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site app.clay.com --profile adithya --url https://app.clay.com/workspaces
```

## Top-Level Routes
- `/workspaces` -> `pages/workspaces.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Inspect Clay Enrichment Tables -> `workflows/inspect-tables.md`

## Human Boundaries
Do not bypass security challenges, email PIN checkpoints, payment steps, or phone verification without notifying the operator.
