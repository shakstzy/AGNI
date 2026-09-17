# Telegram Adapter

The Telegram adapter executes commands directly against the native `telegram` binary.

## Operating Contract

- **Binary**: `/home/shakstzy/.local/bin/telegram` (or ambient `telegram` in PATH).
- **Configuration Location**: Host user configuration at `~/.config/tg/config.json5`.
- **Execution Mode**: Direct binary invocation. No long-running background daemon, polling loops, or internal wrappers.
- **Safety Boundary**: Read-only commands (`check`, `whoami`, `chats`, `read`, `search`, `contact`) do not alter state. Any message send mutates external state; always resolve the exact target and confirm before sending.
- **Write Access**: The CLI operates in read-only mode by default; write commands require write access (`telegram write-access enable`).
