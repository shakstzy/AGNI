# macOS Contacts Adapter

Technical adapter contract for interacting with Apple Contacts.app on the macOS host over pinned Tailscale SSH.

## Operating Contract

- **Binary / Entry**: `macos-contacts` in PATH (symlinked to `.agents/skills/local/macos-contacts/macos-contacts`).
- **Core Script**: `.agents/skills/local/macos-contacts/contacts.py` (dependency-free Python 3).
- **Transport**: BatchMode pinned SSH into the Mac with `UserKnownHostsFile` and dedicated SSH identity key.
- **Connection Configuration**:
  - Resolved cleanly in order:
    1. Ambient environment variables (`MACOS_CONTACTS_HOST`, `MACOS_CONTACTS_USER`, `MACOS_CONTACTS_KNOWN_HOSTS`, `MACOS_CONTACTS_IDENTITY`).
    2. Externalized JSON configuration at `~/.config/hades/apple/apple-config.json` (mode `0600`).
  - Pinned host keys and private keys are strictly externalized in `~/.config/hades/apple/` (mode `0600`).
  - Zero private keys or host records stored in git repository.

## Safety & Boundaries

- Inspect and verify contact IDs before renaming or creating contacts.
- Explicit approval required before creating new contacts or renaming existing contacts (`create`, `rename`).
- Read commands (`status`, `get`, `search`, `find-by-phone`, `find-all-by-phone`) are non-destructive and can be executed freely.
