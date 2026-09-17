---
name: gog
description: Google Workspace CLI (`gog`, gogcli v0.40+) for Gmail, Calendar, Drive, Docs, Sheets, and Tasks across registered accounts.
---

# Gog — Google Workspace CLI

`gog` is installed (Homebrew `gogcli`, v0.40.0). Config at
`~/Library/Application Support/gogcli/`; OAuth tokens live in its keyring —
zero in-repo state.

## AGNI OAuth client

- GCP project: `agni-gog` (gcloud account `adithya@outerscope.xyz`), APIs
  enabled: gmail, calendar-json, drive, docs, sheets, tasks, people.
- OAuth client (Desktop type): `153503573320-efaa9p16ns5sfrpkcp7ghl596lcbnt9l`
  stored via `gog auth credentials set` as client name **`agni`** — pass
  `--client agni` to every `auth add`/call.
- Consent screen: External / Testing; the 12 vault Google accounts are listed
  as test users (aartip3992 and avery@seedboxlabs.co excluded by user).
- Keyring backend: **file** (macOS Keychain hangs headless).
  `export GOG_KEYRING_PASSWORD=$(cat .secrets/gog-keyring-pass)` — the file
  sits at `.secrets/gog-keyring-pass` (git-ignored) alongside the client JSON
  `.secrets/agni-gog-client.json`.

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
export GOG_KEYRING_PASSWORD=$(cat .secrets/gog-keyring-pass)
gog auth add <email> --client agni --timeout 15m \
  --services gmail,calendar,drive,docs,sheets,tasks,contacts,people
```

It auto-opens the URL in the **default browser (Safari)** and spins a
localhost listener. To keep the session in the shared Chrome profile:
close the auto-opened Safari tab, paste the printed URL into Chrome, and
append `&login_hint=<email>&prompt=login` when a different Google account
is already signed in (skips the account chooser — clicks on it don't land
reliably). Default flow timeout is short — always pass `--timeout 15m`.

Unverified-app consent shows "Google hasn't verified this app" → Continue →
scroll → Allow. Enrolled so far: `adithya@outerscope.xyz`.

## Boundaries (harness-enforced)

- Sending email (`gog send`, `gmail send`), Drive deletes, calendar
  removals → REFUSED, escalate to a human.
- `--gmail-no-send` and `--dry-run` exist for extra-safe runs.
