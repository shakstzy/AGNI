# WhatsApp Adapter

The WhatsApp adapter executes commands directly against the native `wacli` binary.

## Operating Contract

- **Binary**: `/home/shakstzy/.local/bin/wacli` (or ambient `wacli` / `whatsapp` in PATH).
- **Store Location**: Host user store at `~/.local/state/wacli` (configurable via `WACLI_STORE_DIR` or `--store`).
- **Execution Mode**: Direct binary invocation. No long-running background daemon, polling loops, or internal wrappers.
- **Safety Boundary**: Read-only commands (`chats list`, `messages list`, `contacts search`, `doctor`) do not alter state. Any message or media send mutates external state; always resolve the exact recipient JID and confirm before sending.
