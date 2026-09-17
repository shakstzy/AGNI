---
name: granola
description: The granola adapter provides command-line access to Granola meeting notes, transcript exports, and workspace folders.
---

# Granola CLI User Guide

The `granola` adapter provides command-line access to Granola meeting notes, transcript exports, and workspace folders.

## Common Operations

### 1. Check Version & Auth
```bash
# Check version
granola --version

# Check auth status
granola auth status
```

### 2. Meetings & Notes
```bash
# List recent meetings (without interactive pager)
granola meeting list --no-pager

# View specific meeting details
granola meeting get <meeting_id> --no-pager
```

### 3. Workspaces & Folders
```bash
# List workspaces
granola workspace list --no-pager

# List folders
granola folder list --no-pager
```
