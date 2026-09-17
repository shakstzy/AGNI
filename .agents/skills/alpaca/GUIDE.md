---
name: alpaca
description: Alpaca Markets Tier-1 CLI for portfolio management, paper & live order execution, market clock, historical bars, and real-time news feeds.
---

# Alpaca Markets CLI Guide

Autonomous paper/live trading, asset positions, market clock, real-time news, and historical market data via Alpaca REST API v2 (`alpaca`).

## Configuration & Credentials

Configuration is resolved in order:
1. `APCA_API_KEY_ID`, `APCA_API_SECRET_KEY`, `APCA_API_BASE_URL` in environment.
2. External config at `~/.config/hades/alpaca.json` (mode 0600).
   ```json
   {
     "key_id": "PK...",
     "secret_key": "...",
     "base_url": "https://paper-api.alpaca.markets",
     "data_url": "https://data.alpaca.markets"
   }
   ```

## CLI Commands

### Account & Portfolio State
```bash
# Check account equity, cash, buying power, and market clock
alpaca status
alpaca status --json

# Check market open/close schedule
alpaca clock
```

### Portfolio Positions
```bash
# View open positions with unrealized P&L
alpaca positions
alpaca positions --json
```

### Order Management
```bash
# View open or recent orders
alpaca orders [--status open|closed|all] [--limit 50]

# Buy shares by quantity or notional dollar amount
alpaca buy AAPL --qty 5
alpaca buy NVDA --notional 500 --type market

# Place limit order with bracket stop-loss and take-profit
alpaca buy PLTR --qty 10 --type limit --limit-price 25.50 --take-profit 30.00 --stop-loss 23.50

# Sell shares or liquidate position
alpaca sell AAPL --qty 5
alpaca sell NVDA --all

# Cancel open orders
alpaca cancel <order_id>
alpaca cancel --all
```

### Market Intelligence & Data
```bash
# Stream latest market headlines or filter by ticker
alpaca news
alpaca news --symbol MSFT --limit 5

# Fetch historical OHLCV bars
alpaca bars NVDA --limit 10
alpaca bars AAPL --timeframe 1Day --limit 30 --json
```
