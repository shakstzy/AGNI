---
site: supabase.com
login_required: true
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# Supabase Dashboard Sitemap

## Overview
Supabase cloud console for project management, PostgreSQL database, authentication, and storage via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site supabase.com --profile adithya --url https://supabase.com/dashboard/projects
```

## Top-Level Routes
- `/dashboard/projects` -> `pages/dashboard.md`
- `/dashboard/project/*/editor` -> `pages/project_overview.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Inspect Supabase Project Status -> `workflows/check-project-health.md`

## Human Boundaries
Do not bypass security challenges, email PIN checkpoints, payment steps, or phone verification without notifying the operator.
