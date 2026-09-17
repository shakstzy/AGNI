---
name: whatsapp
description: WhatsApp CLI adapter for syncing, searching, contacts, and messaging via wacli.
---

# WhatsApp Guide

Local WhatsApp management and messaging via the `wacli` CLI.

## Execution Pattern

WhatsApp commands run directly against the native `wacli` (or `whatsapp`) binary:

```bash
# Diagnostic & store status
wacli doctor

# List recent chats (JSON output for structured parsing)
wacli chats list --limit 20 --json

# List recent messages from a specific chat
wacli messages list --chat <jid> --limit 20 --json

# Search contacts
wacli contacts search "<name>" --limit 10 --json

# Sync new messages on-demand
wacli sync

# Send a text message (requires explicit recipient confirmation)
wacli send text --to <jid> --message "<text>"

# Send a media file (requires explicit recipient confirmation)
wacli send file --to <jid> --file /absolute/path/to/file --caption "<caption>"
```

## Fast Messaging (Single-Turn Execution)

Do not perform multi-turn discovery loops or manually parse JSON just to send a message. Use `msg send` or invoke `wacli send` directly:

```bash
# Preferred single-turn dispatch (auto-resolves contact name and verifies send)
msg send "Adithya" "Hey, running 5 minutes late" --channel whatsapp

# Direct CLI execution if JID is already known
wacli send text --to 15104499964@s.whatsapp.net --message "Hello"

# Send a media file
wacli send file --to <jid> --file /absolute/path/to/file --caption "<caption>"
```

## Contact & Chat Lookups (When Specifically Requested)

Only search contacts or list messages when Adithya explicitly asks to view them:

```bash
# Search contacts
wacli contacts search "<name>" --limit 5

# List recent chats
wacli chats list --limit 10
```

## Security & Safety Rules

1. **Target Confirmation**: Always resolve and confirm the exact JID before executing any remote send command.
2. **Never Retry Uncertain Sends**: If a network timeout or error occurs during send, verify status before retrying.
3. **No Daemons**: Run manual syncs on demand. Do not run unmanaged background sync daemons (`sync --follow`).
4. **Session Protection**: The session store at `~/.local/state/wacli/` contains active keys. Never dump or expose raw session database files.
