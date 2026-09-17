# MCPorter CLI Adapter

Technical adapter contract for MCPorter, a client tool for interacting with Model Context Protocol (MCP) servers, executing tool calls, managing OAuth 2.0 PKCE authentication, and compiling standalone CLIs.

## Operating Contract

- **Binary**: `/home/shakstzy/.local/bin/mcporter` (ambient in PATH).
- **Configuration**: Stored externally in `~/.mcporter/mcporter.json`.
- **Credentials**: Managed in `~/.mcporter/credentials.json`.
- **Execution**: Direct native CLI (`mcporter list`, `mcporter call`, `mcporter auth`, `mcporter generate-cli`).

## Inspect First

```bash
command -v mcporter
mcporter --version
mcporter list
```

## Security & State Boundaries

1. **External Config**: Always use `--scope home` when persisting servers to write to `~/.mcporter/mcporter.json` instead of repository root.
2. **Stateless Repository**: Never commit credential tokens or session data to git.
3. **OAuth Boundary**: Use `--no-browser` when invoking interactive OAuth flows in headless environments.
