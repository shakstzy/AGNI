---
page_id: cards
path: /cards
url_patterns:
  - https://app.mercury.com/cards*
---

# Cards Page (Mercury)

## Visual Anchors
- Navigation link with href `/cards`
- Page heading `Cards`
- Link / button named `Create card` with destination `/issue-card`
- Cards list table showing Type (virtual or physical), Nickname, Spend Limit, and last4

## Actions

### action:open-card-creation
- **pre**: Logged in and on `/cards`.
- **do**: Click `Create card` button / link once.
- **post**: Redirected to `/issue-card` and virtual card creation form is visible.
- **fail**: Login redirect, session expiry, or link missing.
- **recover**: Stop on login/MFA. Inspect live DOM.

### action:freeze-card
- **pre**: Logged in on `/cards`. Named virtual card `signup:<service>` is visible. Signup charge has been verified.
- **do**: Open card details for that nickname and click `Freeze card`.
- **post**: Card status updates to `Frozen`.
- **fail**: Card missing or freeze control not visible.
- **recover**: Do not retry blindly. Confirm state in cards table. Never print full PAN or CVV.
