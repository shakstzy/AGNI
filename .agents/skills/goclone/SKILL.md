---
name: goclone
description: Website mirroring CLI adapter for downloading public websites for offline analysis.
---

# Goclone Guide

Local website mirroring and scraping using the `goclone` CLI.

## Execution Pattern

```bash
# Verify installation
goclone --version

# Mirror a public site to the current directory
goclone https://example.com

# Verify downloaded structure
ls -la example.com/
```

## Security & Approval Boundaries

1. **Working Directory**: Always ensure `pwd` is the intended download destination.
2. **Explicit Approval**: Require approval before running clones.
3. **No Auth/Cookies**: Never clone authenticated pages or pass session cookies without explicit authorization.
