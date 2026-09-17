# Workflow: Check CMG Mortgage Balance & Escrow

Inspect current loan balance, interest rate, and escrow status.

## Steps

1. Launch isolated browser session:
   ```bash
   .agents/skills/browser/cli/browser opencli --site secure.cmghomeloans.com --profile adithya --url https://secure.cmghomeloans.com/dashboard
   ```
2. If redirected to login, retrieve credentials via Bitwarden:
   ```bash
   bw get item "CMG Home Loans (adithya@outerscope.xyz)"
   ```
3. Input username and password. Halt if 2FA or CAPTCHA appears.
4. Extract unpaid principal balance, escrow balance, current interest rate, and next payment amount.
5. Ingest extracted fields into `workspaces/finance/stages/01_ingest/`.
