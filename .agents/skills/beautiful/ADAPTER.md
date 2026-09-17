# Beautiful.ai Local CLI Adapter

Local CLI adapter providing programmatic presentation generation, template discovery, theme retrieval, and slide deck manipulation via Beautiful.ai's official Model Context Protocol (MCP) server.

## Operating Contract

- **Binary**: `/home/shakstzy/.local/bin/beautiful` (backed by MCPorter).
- **Transport**: Remote SSE MCP endpoint (`https://openai-mcp-696419881849.us-central1.run.app/mcp`).
- **Configuration**: Managed in `~/.mcporter/mcporter.json` under server identifier `beautiful-ai`.
- **Authentication**: OAuth 2.0 PKCE authorization flow. Credentials and bearer tokens reside exclusively in `~/.mcporter/credentials.json`.
- **Execution Pattern**: Native subcommands (`beautiful status`, `beautiful list`, `beautiful create`, `beautiful call <tool>`).

## Inspect First

Check configuration and live server connection:

```bash
which beautiful
beautiful status
```

Inspect tool schemas:

```bash
beautiful schema
```

## Security & State Boundaries

1. **No In-Repo State**: Zero credentials, tokens, or session SQLite/JSON files are kept within `HADES`.
2. **Interactive OAuth Authorization**: Run `beautiful auth --no-browser` when authentication is needed. Present the generated URL to Adithya to approve via browser. Once the callback completes, tokens are managed automatically by MCPorter.
3. **Graceful Failures**: If the remote service returns HTTP 401 or expires, invoke `beautiful auth` to re-authorize.
