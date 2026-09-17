---
name: scheduler
description: Scheduled job management — add/list/remove/run recurring commands via the workspace `schedule` CLI backed by crontab.
---

# Scheduler Skill

Timed execution lives in `workspaces/scheduler/` with a `schedule` CLI
wrapping crontab + a jobs manifest (`workspaces/scheduler/jobs.json`).

```bash
workspaces/scheduler/schedule list
workspaces/scheduler/schedule add <name> --cron "*/30 * * * *" --cmd "agni 'check gmail'"
workspaces/scheduler/schedule run <name>          # fire now
workspaces/scheduler/schedule remove <name>
workspaces/scheduler/schedule install             # sync manifest -> crontab
```

- Jobs are tagged `# agni:<name>` in the crontab; `install` rewrites only
  AGNI-managed lines, leaving other entries untouched.
- Logs land in `workspaces/scheduler/logs/<name>.log`.
- Adding/removing jobs mutates the user's crontab — the harness guard asks
  for human approval on `schedule install`/`remove`? No — these are
  reversible; they run freely. Destructive cron wipes (`crontab -r`) are
  refused.
