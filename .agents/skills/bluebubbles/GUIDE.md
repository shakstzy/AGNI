# BlueBubbles User Guide

The BlueBubbles adapter provides iMessage sending, reading, contact queries, and media downloads through the BlueBubbles server.

## Quick Reference

| Action | Command |
| --- | --- |
| Check server status | `bluebubbles status` |
| List recent chats | `bluebubbles chats [--limit 50]` |
| View recent messages | `bluebubbles recent-messages [--limit 5] [--attachments]` |
| View chat history | `bluebubbles messages "<chat_guid>" [--limit 50]` |
| Check message status | `bluebubbles message-status "<message_guid>"` |
| Query contacts | `bluebubbles contacts [address...]` |
| Direct chat lookup | `bluebubbles direct-chat "<phone_or_email>"` |
| Send direct message | `bluebubbles send-direct "<recipient>" "<message>"` |
| Send text to chat | `bluebubbles send-text "<chat_guid>" "<message>" --recipient-type <direct\|group>` |
| Send file | `bluebubbles send-file "<chat_guid>" <file_path> --recipient-type <direct\|group>` |
| Download attachment | `bluebubbles attachment-download "<attachment_guid>" <output_path>` |

## Examples

### 1. Send Message (Direct & Single-Turn)
```bash
# Preferred single-turn dispatch via msg
msg send "+15104499964" "Hey, running 5 minutes late" --channel bluebubbles

# Direct CLI execution
bluebubbles send-direct "+15104499964" "Hey, running 5 minutes late"
```

### 2. Check Server Connectivity
```bash
bluebubbles status
```

### 3. Read Recent Messages (When Requested)
```bash
bluebubbles recent-messages --limit 10
```
