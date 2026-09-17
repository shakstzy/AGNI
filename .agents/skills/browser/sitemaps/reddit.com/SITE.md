---
site: reddit.com
login_required: true
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# Reddit Sitemap

## Overview
Reddit community discussions, subreddit sentiment, topic research, and post drafting via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site reddit.com --profile adithya --url https://www.reddit.com/
```

## Top-Level Routes
- `/` -> `pages/feeds.md`
- `/comments/<id>/...` -> `pages/thread.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Analyze Subreddit Sentiment -> `workflows/subreddit-research.md`

## Human Boundaries
Do not bypass security challenges, email PIN checkpoints, payment steps, or phone verification without notifying the operator.
