---
name: beautiful-ai
description: Programmatic slide deck generation, presentation retrieval, template exploration, and theme management using Beautiful.ai through MCPorter.
---

# Beautiful.ai Guide

Use the `beautiful` CLI to create presentations, inspect decks, query workspace folders, and leverage corporate design themes via Beautiful.ai.

## Execution Patterns

```bash
# Verify connection
beautiful status

# Authenticate or refresh OAuth session
beautiful auth

# Inspect available tools and parameters
beautiful schema

# Search or list user presentations
beautiful list

# List available presentation templates
beautiful templates

# List workspace themes
beautiful themes

# List folders
beautiful folders

# Inspect presentation details and slide widgets
beautiful get <presentationId>

# Export presentation to PDF or PPTX
beautiful export <presentationId> pdf
beautiful export <presentationId> pptx

# Call any underlying MCP tool directly
beautiful call list_presentations query="Groundtruth"
beautiful call review_presentation_outline title="Q3 Review" slides:='[{"title":"Overview","summary":"Summary","slideType":"agenda"}]'
```

## Authentication

When unauthorized or after session expiry, run:
```bash
beautiful auth --no-browser
```
Copy the emitted authorization URL and open it in a browser to authorize the application. Once approved, the local callback server captures the tokens into `~/.mcporter/credentials.json`.
