---
name: context7
description: Query live library documentation, API references, and code examples via Context7 CLI (ctx7).
---

# Context7 Guide

Fetch authoritative, version-specific library documentation and live code examples using the Context7 CLI (`ctx7`).

## Prerequisites & Authentication

1. **Bitwarden API Key Retrieval**:
   Retrieve the Context7 API key in-process from Bitwarden if configured:
   ```bash
   export CONTEXT7_API_KEY="$(bw get item "Context7" 2>/dev/null | jq -r '.fields[] | select(.name=="CONTEXT7_API_KEY").value // .login.password' || echo "")"
   ```

2. **Public Tier Fallback**:
   Context7 supports documentation lookups and library searches without an API key or login under standard public quotas.

3. **Status Check**:
   Inspect current authentication status:
   ```bash
   ctx7 whoami
   ```

## Query Workflows

### 1. Library Resolution

Resolve a library name to its canonical Context7 library ID:

```bash
# General search
ctx7 library react "hooks" --json

# Targeted query
ctx7 library tailwindcss --json
```

Output includes library IDs (e.g. `/reactjs/react.dev`, `/tailwindlabs/tailwindcss`), benchmark scores, trust scores, and available version branches.

### 2. Fetching Documentation & Code Snippets

Retrieve code examples and documentation for a specific concept:

```bash
# Query React docs
ctx7 docs /reactjs/react.dev "useState" --json

# Query Next.js docs
ctx7 docs /vercel/next.js "server actions form handling" --json

# Query Supabase docs
ctx7 docs /supabase/supabase "auth with nextjs ssr" --json
```

For focused results, structure queries around single concepts. When investigating feature interactions, query both explicitly in the same string.

### 3. Version-Specific Documentation

For specific framework versions, append the version tag to the library ID as reported in the library resolution output:

```bash
ctx7 docs /vercel/next.js/v14.3.0 "app router layout" --json
```

### 4. Updating Context7

Check for updates and upgrade to the latest CLI release:

```bash
ctx7 upgrade -y
# or
npm install -g ctx7@latest
```

## Security & Operational Rules

1. **Zero Secret Exposure**: Never write or echo `CONTEXT7_API_KEY` into tracked files, shell histories, or chat transcripts.
2. **Externalized Storage**: Runtime state is managed in `~/.config/context7/`, never inside the HADES repository tree.
3. **Structured Ingestion**: Always pass `--json` when invoking `ctx7` from scripts or autonomous workflows to ensure deterministic parsing.
4. **Headless Guard**: Do not run `ctx7 login` or unflagged `ctx7 setup` in background tasks; use environment-injected API keys or the public tier.
