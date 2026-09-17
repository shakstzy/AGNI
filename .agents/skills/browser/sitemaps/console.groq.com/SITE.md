---
site: console.groq.com
login_required: true
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# Groq Console Sitemap

## Overview
Groq LPU developer console, playground, API keys, rate limits, and token performance logs via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site console.groq.com --profile adithya --url https://console.groq.com/playground
```

## Top-Level Routes
- `/playground` -> `pages/playground.md`
- `/keys` -> `pages/keys.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Benchmark Groq LPU Latency -> `workflows/benchmark-latency.md`

## Human Boundaries
Do not bypass security challenges, email PIN checkpoints, payment steps, or phone verification without notifying the operator.
