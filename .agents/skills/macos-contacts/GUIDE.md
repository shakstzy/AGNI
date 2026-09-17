# macOS Contacts User Guide

The `macos-contacts` adapter connects to Apple Contacts.app on Adithya's personal Mac over pinned SSH.

## Quick Reference

| Action | Command |
| --- | --- |
| Check readiness | `macos-contacts status` |
| Search by name | `macos-contacts search "<name_query>"` |
| Lookup by contact ID | `macos-contacts get "<contact_id>"` |
| Find by phone number | `macos-contacts find-by-phone "<phone>"` |
| Find all matches by phone | `macos-contacts find-all-by-phone "<phone>"` |
| Rename contact | `macos-contacts rename "<contact_id>" "<first_name>" "<last_name>"` |
| Create contact | `macos-contacts create "<first_name>" "<phone>"` |

## Examples

### 1. Check Connectivity
```bash
macos-contacts status
```

### 2. Find Contact by Phone
```bash
macos-contacts find-by-phone "+15551234567"
```

### 3. Retrieve Specific Contact
```bash
macos-contacts get "E2B871D2-8902-4A7B-9E33-87B7575FF5C6:ABPerson"
```
