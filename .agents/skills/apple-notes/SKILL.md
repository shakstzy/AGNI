---
name: apple-notes
description: The apple-notes adapter connects to Apple Notes.app on Adithya's personal Mac over pinned SSH.
---

# Apple Notes User Guide

The `apple-notes` adapter connects to Apple Notes.app on Adithya's personal Mac over pinned SSH.

## Quick Reference

| Action | Command |
| --- | --- |
| Check status | `apple-notes status` |
| List folders | `apple-notes folders` |
| List notes in folder | `apple-notes notes "<folder_name>"` |
| Get note content | `apple-notes get "<note_id>"` |
| Create note | `apple-notes create "<title>" --body "<body>" [--folder "<folder>"]` |
| Append to note | `apple-notes append "<note_id>" --body "<body>"` |
| Delete note | `apple-notes delete "<note_id>" --force` |
| Create folder | `apple-notes create-folder "<folder_name>"` |
| Delete folder | `apple-notes delete-folder "<folder_name>" --force` |

## Examples

### 1. Check Connectivity
```bash
apple-notes status
```

### 2. List Folders
```bash
apple-notes folders
```

### 3. Read a Note
```bash
apple-notes get "x-coredata://..."
```
