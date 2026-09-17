# Firecrawl CLI Adapter

Technical adapter contract for web page scraping, recursive site mapping, and LLM-ready markdown extraction via the native `firecrawl` CLI.

## Operating Contract

- **Binary**: `/home/shakstzy/.local/bin/firecrawl` (or ambient `firecrawl` in PATH).
- **Execution**: Direct native CLI (`firecrawl <command> [flags]`).
- **Runtime Credentials**:
  - Configured via environment variable `FIRECRAWL_API_KEY` or stored config.
  - Zero API keys committed to the repository.

## Safety & Boundaries

- **Secret Exposure Guard**:
  - Never print or commit `FIRECRAWL_API_KEY` in shell outputs or artifacts.
- **Resource Limits**:
  - Limit large recursive site crawls (`--limit <n>`) to prevent excessive credit consumption.
  - Inspection and status queries (`firecrawl --status`, `firecrawl --version`) can be executed freely.
