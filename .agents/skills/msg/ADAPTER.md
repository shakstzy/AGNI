# Unified Messaging Adapter (`msg`)

Technical contract for single-shot, cross-channel messaging dispatch across WhatsApp, BlueBubbles (iMessage), and Telegram.

## Operating Contract

- **Binary / Entry**: `msg` in PATH (symlinked to `.agents/skills/local/msg/msg`).
- **Core Implementation**: `.agents/skills/local/msg/msg.py` (Python 3 standard library).
- **Subordinate Backends**:
  - WhatsApp: `wacli` (local SQLite store, daemonless).
  - BlueBubbles: `bluebubbles` (local REST API via macOS Tailscale HTTPS).
  - Telegram: `telegram` (GramJS session).
- **Deterministic Guarantees**:
  - Resolves contact names to phone numbers/JIDs automatically in a single turn.
  - Verifies transmission and prints concise, verified confirmation.
  - Returns exit code 0 on success, non-zero with stderr on failure.

## Command Reference

| Command | Action | Output Format |
|---|---|---|
| `msg send <target> "<text>"` | Auto-resolve channel and target, dispatch message | `[<channel>] Sent to <name> (<target>): "<text>" (verified)` |
| `msg send <target> "<text>" --channel <ch>` | Explicit channel dispatch (`whatsapp`, `bluebubbles`, `telegram`) | `[<channel>] Sent to <name> (<target>): "<text>" (verified)` |
| `msg resolve <target>` | Resolve recipient name to channel and protocol target | `Resolved: channel=<ch>, target=<id>, display_name=<name>` |
| `msg status` | Check status of all 3 messaging backends | Concise multi-line backend status |
