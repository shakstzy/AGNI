---
name: telegram
description: Telegram CLI adapter for reading, searching, contacts, and messaging via telegram CLI.
---

# Telegram Guide

Local Telegram management and messaging via the `telegram` CLI.

## Execution Pattern

Telegram commands run directly against the native `telegram` binary:

```bash
# Verify session and credentials
telegram check

# View active account identity
telegram whoami

# List chats
telegram chats
telegram chats --type group

# Read messages from a chat
telegram read "<Chat Name or @username>" -n 20

# Search messages across chats
telegram search "<query>"

# Inspect contact info
telegram contact @<username>

## Fast Messaging (Single-Turn Execution)

Do not run pre-inspection discovery loops or write-access queries before sending. Send directly via `msg send` or `telegram send`:

```bash
# Preferred single-turn dispatch via unified dispatcher
msg send "@username" "Hey, running 5 minutes late" --channel telegram

# Direct CLI execution
telegram send "<@username or Chat Name>" "<message>"
```

## Chat & Message Inspection (When Specifically Requested)

Only inspect chats or read messages when Adithya explicitly asks to view them:

```bash
# Verify session
telegram check

# List chats
telegram chats

# Read messages from a chat
telegram read "<Chat Name or @username>" -n 10

# Search messages
telegram search "<query>"
```

## Security & Safety Rules

1. **Target Confirmation**: Always resolve and verify the recipient handle or chat before sending.
2. **Never Retry Uncertain Sends**: If a network timeout or error occurs during send, verify status before retrying.
3. **Write Access Guard**: Write operations must only be enabled for explicit user-approved actions.
4. **Session Protection**: Configuration at `~/.config/tg/config.json5` contains sensitive credentials and session strings. Never dump or expose this file.
