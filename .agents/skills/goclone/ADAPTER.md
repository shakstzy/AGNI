# Goclone CLI Adapter

Use the installed `goclone` CLI to mirror a public website for offline local browsing and static reconstruction. It downloads HTML, styles, scripts, images, and linked assets into a domain-named directory below the current working directory.

## Operating Contract

- **Binary**: `/home/shakstzy/.local/bin/goclone` (or ambient `goclone` in PATH).
- **Execution**: Direct native CLI (`goclone <url>`).
- **Destination**: `goclone` creates a directory named for the target hostname in the current working directory. Always verify the working directory before invoking.

## Inspect First

Before every operation, verify the installed command and its version-specific interface:

```bash
command -v goclone
goclone --version
goclone --help
pwd
```

Confirm the exact target URL and the intended output directory before running `goclone <url>`. Inspect whether the domain-named destination already exists; goclone writes files there and has no explicit output-directory flag.

The installed binary's `--help` is authoritative for flags and defaults.

## Safety & Approval Boundaries

Require explicit approval before any clone operation. Also require explicit approval before:

- Bypassing robots checks with `--robots`;
- Routing traffic through `--proxy_string`;
- Connecting `--browser_endpoint` to a browser;
- Starting a local server with `--serve` / `--servePort`; or
- Opening a browser with `--open`.

Do not pass `--cookie` or use authenticated browser state without explicit authorization. Never use a browser endpoint that could expose unrelated cookies, session data, or personal browsing state. Keep normal robots checks enabled unless their bypass is explicitly approved.

## Scope

This is a profile-free CLI adapter. It owns no credentials, authentication configuration, wrapper, or persistent state.
