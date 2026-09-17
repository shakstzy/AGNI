# Facebook Marketplace CLI Adapter

Technical adapter contract for Facebook Marketplace product sourcing, deals scanning, and listing intelligence.

## Operating Contract

- **Binary**: `/home/shakstzy/HADES/.agents/skills/local/facebook-marketplace/fbm` (alias: `fbm`).
- **Implementation**: `/home/shakstzy/HADES/.agents/skills/local/facebook-marketplace/scripts/cli.py`.
- **Execution Standards**:
  - Direct native execution (`fbm <command> [flags]`).
  - Calls the `facebook-marketplace` MCP server via `mcporter` for deterministic, token-efficient CLI operations.
  - Native preset support for top metro areas (Austin, SF, NYC, LA, Miami, Dallas, Seattle, Chicago).
- **Safety**:
  - Read-only search, listing details, and monitor tracking by default.
  - Session cookies securely managed in `~/.fb-marketplace/cookies.json` or imported from browser profile.
