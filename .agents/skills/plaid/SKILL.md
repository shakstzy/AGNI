---
name: plaid
description: Query linked bank balances, credit card liabilities, investment holdings, and transactions via Plaid CLI (plaid).
---

# Plaid CLI Guide

Fetch banking balances, liabilities, and investment portfolios using the native Plaid CLI (`plaid`).

## Prerequisites & Configuration

1. **CLI Availability**:
   The Plaid CLI is installed at `/home/shakstzy/.local/bin/plaid` (v20260507).
   Verify installation:
   ```bash
   plaid --version
   plaid config
   ```

2. **Bitwarden Integration**:
   Plaid developer keys and API credentials can be loaded in-process from Bitwarden:
   ```bash
   export PLAID_CLIENT_ID="$(bw get item "Atlas Finance" 2>/dev/null | jq -r '.fields[] | select(.name=="PLAID_CLIENT_ID").value' || echo "6689e2629e60dd001a326f6d")"
   export PLAID_SECRET="$(bw get item "Atlas Finance" 2>/dev/null | jq -r '.fields[] | select(.name=="PLAID_SECRET").value' || echo "")"
   ```

3. **Item Status**:
   Inspect currently linked financial institutions:
   ```bash
   plaid item list --json
   ```

## Query Workflows

### 1. Fetching Account Balances

Retrieve all real-time account balances:
```bash
plaid balance --all --json
```

Or query a specific linked institution:
```bash
plaid balance --item <item_id> --json
```

Sample JSON response structure:
```json
{
  "accounts": [
    {
      "account_id": "acc_01",
      "name": "Premier Checking",
      "type": "depository",
      "subtype": "checking",
      "balances": {
        "available": 14250.00,
        "current": 14500.00,
        "iso_currency_code": "USD"
      }
    }
  ]
}
```

### 2. Fetching Liabilities & Debt Data

Query credit cards, mortgages, and student loans:
```bash
plaid liabilities --all --json
```

Returns minimum payments, interest rates (APRs), due dates, and outstanding credit balances.

### 3. Investment Portfolios & Holdings

Fetch securities, ticker symbols, quantities, and valuations:
```bash
plaid investments holdings --all --json
```

### 4. Recent Transactions

Fetch categorized transactions across linked accounts:
```bash
plaid transactions --all --json
```

## Security & Operational Rules

1. **Zero Secret Exposure**: Never write or print raw API secrets, access tokens, or Bitwarden passwords into logs or transcripts.
2. **Deterministic Output**: Always supply `--json` for programmatic consumption by `workspaces/finance`.
3. **Headless Execution**: Do not run interactive browser link flows (`plaid link`) without explicit user presence.
