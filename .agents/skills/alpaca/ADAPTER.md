# Alpaca Markets Adapter

The Alpaca Markets adapter provides native CLI execution against Alpaca's Paper and Live REST trading & data APIs.

## Operating Contract

- **Binary / Entry**: `.agents/skills/local/alpaca/alpaca` or ambient `alpaca` in PATH (symlinked to `/home/shakstzy/.local/bin/alpaca`).
- **Core Script**: `.agents/skills/local/alpaca/alpaca.py` (dependency-free Python 3 using `urllib.request`).
- **Credentials**: Resolved in priority order:
  1. Environment variables `APCA_API_KEY_ID`, `APCA_API_SECRET_KEY`, `APCA_API_BASE_URL`.
  2. External JSON configuration at `~/.config/hades/alpaca.json` (mode 0600).
- **Execution Standards**: Deterministic mutation with `--json` option across all subcommands. Zero secrets are ever printed to logs or stdout.
