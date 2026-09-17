---
workflow_id: create-virtual-card
intent: issue temporary Mercury virtual card for service signups
driver: Browser Use CLI 3.0
---

# Workflow: Create Virtual Card (Mercury)

## Goal
Issue one isolated Virtual debit card named `signup:<service>` with a $5 monthly spending limit for a specific service signup. Freeze after the initial verification charge.

## Safety & Boundaries
- **Strict Limit**: Default to $5 monthly cap to prevent runaway trial billings.
- **Zero PAN/CVV Logging**: Never print or commit 16-digit PAN, CVV, or full cardholder details into logs, transcripts, or git.
- **Identifier Contract**: Only output `nickname` and `last4`.
- **Idempotency**: Never click `Create card` more than once if response is delayed. Always verify via `/cards`.

## Verified Action Sequence
1. Attach to Mercury profile `adithya` on port 9269 (`BU_CDP_URL=http://127.0.0.1:9269`).
2. Navigate to `https://app.mercury.com/cards`.
3. Verify authenticated state. Stop immediately if prompted for MFA, SMS OTP, or password.
4. Click `Create card` to navigate to `https://app.mercury.com/issue-card`.
5. Select `Virtual` card type.
6. Enter nickname `signup:<service>`.
7. Set spending limit to `$5.00 monthly`.
8. Click `Create card` once.
9. Verify issuance confirmation and extract `last4`.
10. Once the signup verification charge is confirmed, navigate back to `/cards` and freeze the card.

## Result Contract
| Field | Description |
| --- | --- |
| `status` | `issued` upon success, `frozen` after freeze, or `uncertain` |
| `nickname` | `signup:<service>` identifier |
| `last4` | Visible 4 digits only |
