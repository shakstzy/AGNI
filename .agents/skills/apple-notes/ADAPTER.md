# Apple Notes Adapter

Technical adapter contract for interacting with Notes.app on the macOS host over pinned Tailscale SSH.

## Operating Contract

- **Binary / Entry**: `apple-notes` in PATH (symlinked to `.agents/skills/local/apple-notes/apple-notes`).
- **Core Script**: `.agents/skills/local/apple-notes/notes.py` (dependency-free Python 3).
- **Transport**: BatchMode pinned SSH into the Mac with `UserKnownHostsFile` and dedicated SSH identity key.
- **Connection Configuration**:
  - Resolved cleanly in order:
    1. Ambient environment variables (`MACOS_NOTES_HOST`, `MACOS_NOTES_USER`, `MACOS_NOTES_KNOWN_HOSTS`, `MACOS_NOTES_IDENTITY`).
    2. Externalized JSON configuration at `~/.config/hades/apple/apple-config.json` (mode `0600`).
    3. Legacy profile fallback if present.
  - Pinned host keys and private keys are strictly externalized in `~/.config/hades/apple/` (mode `0600`).
  - Zero private keys or host records stored in git repository.

## Safety & Boundaries

- Protected folders (`Notes`, `archive`, `Imported Notes`) cannot be deleted.
- Deletions require the `--force` flag.
- Explicit approval required before creating notes, appending to notes, or deleting notes/folders (`create`, `append`, `delete`, `delete-folder`).
- Read commands (`status`, `folders`, `notes`, `get`) are non-destructive and can be executed freely.
