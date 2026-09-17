---
name: apple
description: Apple Account / iCloud access on this Mac — sign-in state, Contacts (AddressBook), Messages, and iCloud dataclasses. Pair with ios skill for simulators.
---

# Apple / iCloud

This Mac is signed into the Apple Account **adithya.shak.kumar@gmail.com** (name: Adithya Kumar).

## Sign-in flow (done)

System Settings → Sign in with your Apple Account → email + password (Bitwarden vault item `card.apple.com`) → 6-digit 2FA code is SMS'd to the user's trusted phone (number ending `11`) — paste code into the segmented field via `pbcopy` + `cmd+v` (typing can drop digits into the wrong boxes).

Verify:

```sh
defaults read MobileMeAccounts Accounts | grep AccountID   # expect adithya.shak.kumar@gmail.com
sqlite3 ~/Library/Accounts/Accounts4.sqlite \
  'select ZUSERNAME from ZACCOUNT where ZACCOUNTTYPEDESCRIPTION like "%iCloud%"'
```

## Access surfaces

| Data | Path / tool |
|---|---|
| Contacts | `~/Library/Application Support/AddressBook/AddressBook-v22.abcddb` (Contacts.app, or `sqlite3` read-only copy) |
| Messages | `~/Library/Messages/chat.db` (read-only; Full Disk Access may be required) |
| iCloud Drive | `~/Library/Mobile Documents/com~apple~CloudDocs/` |
| Reminders/Notes | their .sqlite stores under `~/Library/` (dataclasses provisioned in MobileMeAccounts) |

Dataclass toggles live under System Settings → Apple Account → iCloud. "Some iCloud Data Isn't Syncing" banner may appear until the first sync completes.

## Rules

- Never print Apple ID credentials; fetch from `bw` per the auth skill.
- 2FA codes go ONLY into the same live dialog that requested them — each resend invalidates the previous code.
- Do not sign out, change the Apple ID password, or toggle iCloud security settings without explicit user instruction.
