# Unified Messaging Guide (`msg`)

Single-turn messaging router across WhatsApp, BlueBubbles (iMessage), and Telegram with automatic contact resolution.

## Instant Execution (No Multi-Turn Pre-Inspection)

Never perform discovery loops or search contacts across multiple turns before sending. Pass the person's name or target directly to `msg send`:

```bash
# 1. Send via auto-detected channel (or specify --channel)
msg send "Adithya" "Hey, running 5 minutes late"
msg send "Mom" "I am on my way" --channel whatsapp
msg send "+15104499964" "Test message" --channel bluebubbles
msg send "@shakstzy" "Status update ready" --channel telegram

# 2. Check messaging system health
msg status

# 3. Dry-run recipient resolution
msg resolve "Adithya"
```

## Routing Rules

- If the recipient starts with `@` -> routes to Telegram.
- If the recipient contains `@s.whatsapp.net` or is in WhatsApp contacts -> routes to WhatsApp.
- If the recipient is an E.164 phone number (`+1...`) -> routes to BlueBubbles (iMessage) if online, otherwise WhatsApp.
- If the channel is explicitly provided (`--channel <ch>`), routes strictly to that backend.
