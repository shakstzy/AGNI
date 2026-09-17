---
name: gog
description: Google Workspace CLI (`gog`, gogcli v0.40+) for Gmail, Calendar, Drive, Docs, Sheets, and Tasks across registered accounts.
---

# Gog — Google Workspace CLI

`gog` is installed (Homebrew `gogcli`, v0.40.0). Config at
`~/.config/gogcli/`; OAuth tokens live in its keyring — zero in-repo state.

## Execution

- Always target an account explicitly: `--account=<email>` (or `-a`).
- Discover accounts: `gog auth list --json`.
- Deterministic output: `--json --results-only`; exploratory calls get
  `--readonly`.

```bash
gog status
gog gmail messages search "is:unread" --account=<email> --json --results-only
gog calendar events list --calendar=primary --account=<email> --json --results-only
gog drive search "quarterly" --account=<email> --json --results-only
```

## Auth

```bash
gog auth add <email> --services="gmail,calendar,drive,docs,sheets"
```

Prints an OAuth URL — the user completes consent in the browser. No
accounts are registered yet on this machine; add them as needed.

## Boundaries (harness-enforced)

- Sending email (`gog send`, `gmail send`), Drive deletes, calendar
  removals → REFUSED, escalate to a human.
- `--gmail-no-send` and `--dry-run` exist for extra-safe runs.
