---
name: apple-reminders
description: The apple-reminders adapter connects to Apple Reminders.app on Adithya's personal Mac over pinned SSH.
---

# Apple Reminders User Guide

The `apple-reminders` adapter connects to Apple Reminders.app on Adithya's personal Mac over pinned SSH.

## ADHD Focus Flow

The system is configured around an ADHD focus workflow:
- **`Inbox`**: Quick triage capturing ground.
- **`Today`**: Soft cap of 3 open tasks. Focus list.
- **`Someday`**: Parking lot for deferred tasks.

## Quick Reference

| Action | Command |
| --- | --- |
| Check status | `apple-reminders status` |
| View today focus | `apple-reminders now` |
| List reminder lists | `apple-reminders lists` |
| View items in list | `apple-reminders show "<list_name>" [--completed]` |
| Quick capture to Inbox | `apple-reminders capture "<title>" [--notes "<notes>"]` |
| Add to specific list | `apple-reminders add "<title>" --list "<list_name>" [--notes "<notes>"]` |
| Complete reminder | `apple-reminders complete "<reminder_id>"` |
| Promote to Today | `apple-reminders promote "<reminder_id>" [--force]` |
| Park in Someday | `apple-reminders park "<reminder_id>"` |
| Move reminder | `apple-reminders move "<reminder_id>" --list "<list_name>"` |
| Delete reminder | `apple-reminders delete "<reminder_id>" --force` |
| Create list | `apple-reminders create-list "<list_name>"` |
| Delete list | `apple-reminders delete-list "<list_name>" --force` |

## Examples

### 1. View Current Focus
```bash
apple-reminders now
```

### 2. Capture a Thought
```bash
apple-reminders capture "Review quarterly numbers" --notes "Sent via Slack"
```

### 3. Complete Task
```bash
apple-reminders complete "x-apple-reminder://..."
```
