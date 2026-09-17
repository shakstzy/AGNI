# Apple Reminders Adapter

Technical adapter contract for interacting with Reminders.app on the macOS host over pinned Tailscale SSH.

## Operating Contract

- **Binary / Entry**: `apple-reminders` in PATH (symlinked to `.agents/skills/local/apple-reminders/apple-reminders`).
- **Core Script**: `.agents/skills/local/apple-reminders/reminders.py` (dependency-free Python 3).
- **Transport**: BatchMode pinned SSH into the Mac with `UserKnownHostsFile` and dedicated SSH identity key.
- **Connection Configuration**:
  - Resolved cleanly in order:
    1. Ambient environment variables (`MACOS_REMINDERS_HOST`, `MACOS_REMINDERS_USER`, `MACOS_REMINDERS_KNOWN_HOSTS`, `MACOS_REMINDERS_IDENTITY`).
    2. Externalized JSON configuration at `~/.config/hades/apple/apple-config.json` (mode `0600`).
    3. Legacy profile fallback if present.
  - Pinned host keys and private keys are strictly externalized in `~/.config/hades/apple/` (mode `0600`).
  - Zero private keys or host records stored in git repository.

## Safety & Boundaries

- Protected lists (`Inbox`, `Today`, `Someday`) cannot be deleted.
- Deletions require the `--force` flag.
- The `Today` list has a soft cap of 3 open items; promoting items beyond the cap requires `--force`.
- Explicit approval required before creating reminders, moving, promoting, completing, or deleting reminders (`add`, `capture`, `move`, `promote`, `complete`, `delete`).
- Read commands (`status`, `lists`, `now`, `show`) are non-destructive and can be executed freely.
