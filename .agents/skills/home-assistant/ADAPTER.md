# Home Assistant Adapter

The Home Assistant adapter connects to Adithya's Home Assistant instance via its official REST API.

## Operating Contract

- **Binary / Entry**: `.agents/skills/local/home-assistant/ha` or ambient `ha` in PATH (links to `/home/shakstzy/HADES/.agents/skills/local/home-assistant/ha`).
- **Core Script**: `.agents/skills/local/home-assistant/home_assistant.py` (dependency-free Python 3).
- **Credentials**: Resolved cleanly in order:
  1. Ambient environment variables `HOME_ASSISTANT_URL` and `HOME_ASSISTANT_TOKEN`.
  2. Externalized JSON configuration at `~/.config/hades/home-assistant.json` (mode 0600).
  3. Legacy environment migration fallback.
  Credentials are never committed to the git repository.
- **Redaction**: Access tokens are automatically scrubbed and redacted from error responses and JSON output.

## Command Reference

| Subcommand | Description | Syntax |
| --- | --- | --- |
| `act` | Parse natural intent, dispatch in parallel, and verify state | `ha act "<phrase>"` or `ha turn on <targets...>` |
| `on` | Turn on one or more entities, aliases, or groups with verification | `ha on <target...> [--no-verify] [--json]` |
| `off` | Turn off one or more entities, aliases, or groups with verification | `ha off <target...> [--no-verify] [--json]` |
| `toggle` | Toggle one or more entities, aliases, or groups with verification | `ha toggle <target...> [--no-verify] [--json]` |
| `state` | Get current state of entity, alias, or group (concise by default) | `ha state <target...> [--json]` |
| `upstairs` | Shorthand control for upstairs fan & light | `ha upstairs <on\|off\|state>` |
| `downstairs` | Shorthand control for downstairs kitchen & living switches | `ha downstairs <on\|off\|state>` |
| `devices` | List indexed devices, groups, and aliases locally (<5ms) | `ha devices [--domain <domain>] [-b]` |
| `sync` | Sync all Home Assistant entities into local index file | `ha sync` |
| `alias` | View or bind custom entity aliases | `ha alias [<name>] [<entity_id>]` |
| `states` | List states (optionally filtered by domain) | `ha states [--domain <domain>] [-b]` |
| `status` | Check server connectivity and system health | `ha status` |
| `config` | Retrieve Home Assistant core configuration | `ha config` |
| `services` | List available service domains and calls | `ha services` |
| `call` | Invoke a service and read back new state | `ha call <domain> <service> --entity <id> [--data '<json>']` |
| `errors` | Stream recent error logs from Home Assistant | `ha errors` |
| `check-config` | Trigger remote configuration validation | `ha check-config` |
