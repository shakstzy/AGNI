---
page_id: issue-card
path: /issue-card
url_patterns:
  - https://app.mercury.com/issue-card*
---

# Issue Card Page (Mercury)

## Visual Anchors
- Form heading: `Create a card`
- Card type toggle / radio: `Virtual` (default) vs `Physical`
- Form fields: Cardholder, Card nickname, Source account, Limit type, Spending limit
- Spending limit default for signup cards: `$5 monthly`
- Submit control: button named `Create card`

## Actions

### action:configure-virtual-card
- **pre**: Logged in on `/issue-card` with target service name known.
- **do**:
  1. Confirm `Virtual` card type is selected.
  2. Set Card nickname to `signup:<service>` (e.g. `signup:openai`).
  3. Set Limit type to `Monthly` and amount to `$5.00`.
  4. Leave merchant controls unset unless specified.
- **post**: Configured fields match required parameters.
- **fail**: Form validation error or missing field.
- **recover**: Reset fields; do not raise limit above $5 without explicit instruction.

### action:issue-card
- **pre**: Form configured with `Virtual`, nickname `signup:<service>`, and `$5 monthly`.
- **do**: Click `Create card` once.
- **post**: Confirmation dialog displayed or card appears in `/cards` with assigned last4.
- **fail**: Network error, timeout, or ambiguity.
- **recover**: Do not click `Create card` a second time. Navigate to `/cards` and check if the card was issued.
- **evidence**: Report nickname and `last4` only. Never log PAN or CVV.
