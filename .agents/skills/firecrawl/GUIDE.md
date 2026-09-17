# Firecrawl CLI User Guide

The `firecrawl` adapter converts live web pages and entire domains into clean, structured Markdown ready for LLM processing.

## Common Operations

### 1. Check Version & Status
```bash
# Check version and account credit status
firecrawl --status

# Output version number
firecrawl --version
```

### 2. Scrape Single URL
```bash
# Scrape webpage to clean Markdown
firecrawl scrape "https://example.com"

# Scrape and save directly to file
firecrawl scrape "https://example.com" -o output.md
```

### 3. Crawl Website
```bash
# Crawl site with page limit
firecrawl crawl "https://example.com" --limit 10

# Map all URLs discovered across domain
firecrawl map "https://example.com"
```
