# Postiz CLI User Guide

The `postiz` adapter provides command-line interaction with Postiz social media scheduling and post management.

## Common Operations

### 1. Check Version & Help
```bash
# Check version
postiz --version

# View available subcommands
postiz --help
```

### 2. List & Inspect Posts
```bash
# List all configured and scheduled posts
postiz posts:list

# Change post status (e.g. to draft)
postiz posts:status <post_id> draft
```

### 3. Create Posts
```bash
# Create post draft
postiz posts:create
```
