# BlueBubbles Adapter

Technical adapter contract for iMessage communication via the BlueBubbles REST API.

## Operating Contract

- **Binary / Entry**: `bluebubbles` in PATH (symlinked to `.agents/skills/local/bluebubbles/bluebubbles`).
- **Core Script**: `.agents/skills/local/bluebubbles/bluebubbles.py` (dependency-free Python 3).
- **Backend**: BlueBubbles server running on macOS host, accessible over Tailscale HTTPS.
- **Credentials & Configuration**:
  - Resolved cleanly in order:
    1. Ambient environment variables `BLUEBUBBLES_URL` and `BLUEBUBBLES_PASSWORD`.
    2. Externalized JSON configuration at `~/.config/hades/bluebubbles.json` (mode `0600`).
    3. Legacy profile fallback if present.
  - Zero credentials or tokens committed to git repository.
- **Redaction**: The server password is automatically redacted from all API output and error strings.

## Safety & Boundaries

- Treat outgoing messages as real-world communications.
- Explicit approval required before sending messages or media (`send-direct`, `send-text`, `send-file`).
- Read commands (`status`, `chats`, `recent-messages`, `messages`, `contacts`) are non-destructive and can be executed freely for inspection.
