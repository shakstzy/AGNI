---
name: mcporter
description: Model Context Protocol (MCP) server configuration, discovery, authentication, tool invocation, and CLI generation.
---

# MCPorter Guide

Interact with MCP servers and generate standalone CLI tools using `mcporter`.

## Execution Patterns

```bash
# Verify installation
mcporter --version

# List configured servers
mcporter list

# Inspect tools and schemas for a server
mcporter list <server> --schema

# Add a remote SSE/HTTP MCP server to user configuration
mcporter config add --scope home <server> <url>

# Run OAuth authorization
mcporter auth <server> --no-browser

# Call an MCP tool directly
mcporter call <server>.<tool> [arg1=val1 arg2=val2]

# Generate standalone CLI executable
mcporter generate-cli <server> --bundle <output.mjs>
```
