---
name: x-cockpit
description: The x-cockpit adapter performs autonomous Twitter/X virality mining, follower-to-conversion auditing, creator uniqueness classification, and cross-account breakout trend clustering.
---

# Twitter Virality Cockpit CLI User Guide

The `x-cockpit` adapter performs autonomous Twitter/X virality mining, follower-to-conversion auditing, creator uniqueness classification, and cross-account breakout trend clustering.

## Architecture & Levers

1. **Follower-to-Conversion Ratio**:
   - `Reach Multiple = Impressions / max(Followers, 100)`
   - `High-Intent Conversions = Likes + (2 * Reposts) + (3 * Bookmarks)`
   - Identifies whether a tweet broke out algorithmically ($>3\times$ followers) or just relied on massive account size.

2. **Uniqueness Classification**:
   - **`CREATOR_DEPENDENT`** (Low Transferability): Company funding announcements, ARR milestones, family events, private hiring DMs, specific credentials.
   - **`REPEATABLE_BREAKOUT_STYLE`** (High Transferability): Contrarian outcomes, dirty secrets, under-the-hood architecture teardowns, 99% vs 1% splits, paradoxes, timelines, and curated opportunity stashes.

3. **Cross-Account Trend Clustering**:
   - Groups posts sharing the same syntactic archetype across $\ge 2$ distinct accounts.
   - Computes average reach multiple and flags confirmed breakout trends (`🚨 CONFIRMED BREAKOUT TREND`).
   - Generates drop-in reproduction copy tailored for Shak (@shakstzy).

## Common Operations

### 1. Scan Topic / Niche
```bash
# Scan recent top tweets for topic and cluster breakout trends
x-cockpit scan "physical ai" --count 15

# Also available via cockpit runner
cockpit x scan "coding agents" --count 10
```

### 2. Evaluate a Single Post Copy
```bash
# Evaluate viral archetype and transferability score
x-cockpit evaluate "All the money in Physical AI is going to be made selling outcomes not robots." \
  --followers 8085 --views 24450 --likes 86 --reposts 15 --bookmarks 21
```

### 3. Save Structured JSON Intelligence
```bash
x-cockpit scan "autonomous agents" -o ./virality_report.json
```
