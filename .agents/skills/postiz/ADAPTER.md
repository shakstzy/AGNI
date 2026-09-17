# Postiz CLI Adapter

Technical adapter contract for managing multi-platform social media scheduling, post creation, and channel dispatch via the native `postiz` CLI.

## Operating Contract

- **Binary**: `/home/shakstzy/.local/bin/postiz` (or ambient `postiz` in PATH).
- **Execution**: Direct native CLI (`postiz <command> [options]`).
- **Runtime Credentials**:
  - Configured via environment variables (`POSTIZ_API_KEY`, `POSTIZ_URL`) or local config.
  - Zero API keys committed to the repository.

## Safety & Boundaries

- **Secret Exposure Guard**:
  - Never print or commit Postiz API keys or connected social account tokens.
- **Approval Boundaries**:
  - Ask for explicit approval before publishing live posts or deleting scheduled posts.
  - Creating draft posts and read-only inspections (`postiz posts:list`, `postiz --version`) can be executed freely.
