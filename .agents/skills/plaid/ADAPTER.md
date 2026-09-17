# Plaid CLI (plaid) Adapter

Technical adapter contract for interacting with linked banking, credit, and investment accounts via the Plaid CLI (`plaid`).

## Operating Contract

- **Binary**: `/home/shakstzy/.local/bin/plaid` (or ambient `plaid` in PATH).
- **Environment**: Client ID `6689e2629e60dd001a326f6d`, Team ID `6689e2629e60dd001a326f6c`.
- **Selected Environment**: `production` (fallback to `sandbox` for testing).
- **Authentication Contract**:
  - Plaid CLI stores local configuration in `~/.config/plaid/`.
  - API keys and client secrets are retrieved in-process from Bitwarden under item `"dashboard.plaid.com (adithya@outerscope.xyz)"` or `"Atlas Finance"`.
  - Non-interactive automation passes `--json` for structured output.
  - **Headless Guard**: Never invoke interactive `plaid login` or `plaid link` without headless tokens or explicit human interaction prompts.

## Operating Interface

1. **Account Balances**:
   ```bash
   plaid balance --all --json
   plaid balance --item <item_id> --json
   ```
   Returns real-time available and current balances, currency, and account types (checking, savings, credit, loan).

2. **Liabilities**:
   ```bash
   plaid liabilities --all --json
   plaid liabilities --item <item_id> --json
   ```
   Returns credit card APRs, minimum payments, due dates, student loan details, and mortgage balances where supported.

3. **Investments & Holdings**:
   ```bash
   plaid investments holdings --all --json
   ```
   Returns security holdings, ticker symbols, quantities, cost bases, and market valuations.

4. **Transactions**:
   ```bash
   plaid transactions --all --json
   ```
   Returns settled and pending account transactions with category taxonomies.

5. **Item Management & Status**:
   ```bash
   plaid item list --json
   plaid config
   plaid --version
   ```

## Storage & Boundary Contract

- Local configuration: `~/.config/plaid/` (externalized from the HADES repository).
- No secrets, tokens, or raw bank credentials are saved in git tracking.
- Output from CLI operations is ingested directly by `workspaces/finance/stages/01_ingest/`.
