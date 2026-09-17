# Google Trends CLI User Guide

The `google-trends` adapter provides deterministic Tier 1 access to Google Trends data for tracking search volume velocity and breakout search surges.

## Binary & Aliases
- `google-trends` (canonical)
- `gtrends` (alias)
- `trends` (alias)

## Common Operations

### 1. Status Check
Check stream connectivity, RSS feed latency, and Chrome CDP profile readiness:
```bash
google-trends status
# With raw JSON output
google-trends status --json
```

### 2. Real-Time & Daily Trending Searches
Retrieve top trending search queries with approximate search volume, growth velocity, and recency:
```bash
# Top 20 trending searches in the US
google-trends trending

# Specific country code and limit
google-trends trending --geo US --limit 10
google-trends trending --geo GB --limit 15

# Force fast RSS mode (<700ms) or deep browser extraction
google-trends trending --mode fast
google-trends trending --mode browser --limit 10

# Output structured JSON
google-trends trending --limit 10 --json
```

### 3. Query Exploration & Interest Over Time
Analyze a specific keyword or topic across historical windows (daily interest data points from 0 to 100):
```bash
# Explore search interest over past 90 days (default)
google-trends explore "ice bath"

# Explore over specific timeframe (1d, 7d, 1m, 3m, 12m)
google-trends explore "ai agents" --time 1m --geo US
google-trends explore "dropshipping" --time 12m

# Structured JSON
google-trends explore "solana" --json
```

### 4. Query Volume Velocity
Calculate exact velocity metrics (7-day, 14-day, 30-day moving averages, trend slope, peak score, and momentum classification):
```bash
# Calculate volume velocity for a query
google-trends velocity "ice bath"
google-trends velocity "ai agents" --time 1m

# JSON format for automated pipelines
google-trends velocity "creatine" --json
```

### 5. Breakout Search Tracking
Identify searches with explosive growth velocity (>500% or Google "Breakout" status):
```bash
# Discover real-time breakout searches across the region
google-trends breakout
google-trends breakout --geo US --limit 10

# Discover breakout related queries for a specific seed topic
google-trends breakout --query "ai agents"
google-trends breakout --query "dropshipping" --time 3m
google-trends breakout --query "supplements" --json
```

### 6. Multi-Query Velocity Comparison
Compare search volume momentum and velocity classifications across multiple keywords side by side:
```bash
google-trends compare "openai" "anthropic" "deepseek" --time 1m
google-trends compare "shopify" "woocommerce" "amazon" --time 3m --geo US
```
