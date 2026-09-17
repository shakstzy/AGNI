# Notion CLI (ntn) Adapter

Technical adapter contract for interacting with Notion workspaces, databases, pages, and API endpoints via the native `ntn` CLI.

## Operating Contract

- **Binary**: `/home/shakstzy/.local/bin/ntn` (or ambient `ntn` in PATH).
- **Execution**: Direct native CLI (`ntn <command> [flags]`).
- **Context**: Configured via `ntn login` or environment variable `NOTION_TOKEN` / `NOTION_WORKSPACE_ID`.
- **Runtime Credentials**:
  - Externalized in `~/.config/ntn/`.
  - Zero workspace integration tokens committed to repository.

## Safety & Boundaries

- **Secret Exposure Guard**:
  - Never print or commit Notion secret integration tokens (`ntn_*` or `secret_*`).
- **Approval Boundaries**:
  - Ask for explicit approval before deleting pages, updating database schemas, or executing bulk deletions.
  - Read-only inspections (`ntn --version`, `ntn datasources list`, `ntn pages list`) can be executed freely.
