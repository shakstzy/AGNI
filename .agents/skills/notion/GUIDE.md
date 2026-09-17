# Notion CLI (ntn) User Guide

The `notion` adapter provides command-line interaction with Notion workspaces, databases, pages, and API resources.

## Common Operations

### 1. Check Version & Status
```bash
# Check CLI version
ntn --version

# Check authenticated identity
ntn whoami

# Health / diagnostics
ntn doctor
```

### 2. Pages & Data Sources
```bash
# Retrieve a page as Markdown
ntn pages get <page_id>

# Create a page from Markdown
ntn pages create --content '# Title\n\nBody'

# Query a data source / database
ntn datasources query <database_or_datasource_id>

# Resolve a database ID to its data source IDs
ntn datasources resolve <database_id>
```

### 3. Direct Notion API
```bash
# Query current bot user / workspace metadata
ntn api /v1/users/me

# Query a database
ntn api /v1/databases/<database_id>/query
```
