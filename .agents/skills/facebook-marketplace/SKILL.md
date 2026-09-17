---
name: facebook-marketplace
description: The facebook-marketplace adapter (fbm) provides deterministic Tier 1 access to Facebook Marketplace listings, deals search, item details, and keyword monitors.
---

# Facebook Marketplace CLI Guide

The `facebook-marketplace` adapter (`fbm`) provides deterministic Tier 1 access to Facebook Marketplace listings, deals search, item details, and keyword monitors.

## Binary & Invocation
- Canonical command: `fbm` (or `.agents/skills/local/facebook-marketplace/fbm`)

## Common Operations

### 1. Status Check
Check session cookie validity, browser profile integration, and active search monitors:
```bash
fbm status
fbm status --json
```

### 2. Authentication
Import cookies from browser profile, file, or raw cookie string:
```bash
# Check current authentication status
fbm auth

# Save cookie string
fbm auth --cookie "c_user=...; xs=...;"

# Import cookies from exported JSON
fbm auth --file /path/to/cookies.json
```

### 3. Search Listings
Search items across metro presets or specific coordinates:
```bash
# Search within a preset market (austin, sf, nyc, la, miami, dallas, seattle, chicago)
fbm search "macbook pro" --market austin

# Search with price filters and radius
fbm search " Herman Miller" --market sf --min-price 100 --max-price 500 --radius 40

# Structured JSON output
fbm search "iphone 15" --market nyc --json
```

### 4. Listing Details
Inspect a specific listing by ID:
```bash
fbm get 123456789012345
fbm get 123456789012345 --json
```

### 5. Monitor Keywords
List or register persistent search monitors:
```bash
# List active monitors
fbm monitor list

# Create a monitor
fbm monitor add --query "eames chair" --market austin --max-price 400
```
