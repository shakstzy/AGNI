# Granola CLI Adapter

Technical adapter contract for managing Granola meeting notes, transcripts, folders, and workspace summaries via the native `granola` CLI.

## Operating Contract

- **Binary**: `/home/shakstzy/.local/bin/granola` (or ambient `granola` in PATH).
- **Execution**: Direct native CLI (`granola <command> [subcommand] [flags]`).
- **Formatting**: Use `--no-pager` for non-interactive scripting.
- **Runtime Credentials**:
  - Auth tokens stored in `~/.config/granola/` or local keychain.
  - Zero token secrets committed to repository.

## Safety & Boundaries

- **Secret Exposure Guard**:
  - Never print or commit Granola session tokens or refresh keys.
- **Approval Boundaries**:
  - Ask for explicit approval before deleting meetings or folders.
  - Read-only inspections (`granola --version`, `granola meeting list`, `granola workspace list`) can be executed freely.
