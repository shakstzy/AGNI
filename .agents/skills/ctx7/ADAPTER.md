# Context7 CLI (ctx7) Adapter

Technical adapter contract for fetching live library documentation, API references, and code examples via the Context7 CLI (`ctx7`).

## Operating Contract

- **Binary**: `/home/shakstzy/.local/bin/ctx7` (or ambient `ctx7` in PATH).
- **Authentication Contract**:
  - Non-interactive automation uses the `CONTEXT7_API_KEY` environment variable.
  - Stored credential session: `~/.config/context7/credentials.json` (mode 0600; externalized in user home, disposable runtime state).
  - **Unauthenticated Fallback**: Documentation queries and library resolution execute without credentials under standard public rate limits.
  - **Headless Guard**: Never invoke bare `ctx7 login` or interactive `ctx7 setup` in automated pipelines without explicit non-interactive arguments or pre-configured API keys, as they launch browser OAuth flows.
  - Optional telemetry suppression: `CTX7_TELEMETRY_DISABLED=1`.

## Operating Interface

1. **Library Resolution**:
   ```bash
   ctx7 library <name> [query] [--json]
   ```
   Resolves a library name to a Context7 library identifier (e.g., `/reactjs/react.dev`, `/vercel/next.js`).

2. **Documentation Query**:
   ```bash
   ctx7 docs <libraryId> <query> [--json]
   ```
   Retrieves targeted code snippets, API signatures, and documentation guides. Pass `--json` for machine-parseable structured output.

3. **Status & Inspection**:
   ```bash
   ctx7 whoami
   ctx7 --version
   ```

4. **Upgrade**:
   ```bash
   ctx7 upgrade -y
   # or
   npm install -g ctx7@latest
   ```

## Storage & Boundary Contract

- Configuration directory: `~/.config/context7/` (outside the HADES repository tree).
- State directory: `~/.local/state/context7/`.
- No credentials, tokens, or temporary cache files are stored within the git repository.
- Credential storage is externalized to Bitwarden under item `"Context7"`.
