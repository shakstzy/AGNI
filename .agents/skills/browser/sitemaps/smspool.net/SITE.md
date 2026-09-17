---
site: smspool.net
login_required: true
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# SMSPool Sitemap

## Overview
SMSPool temporary non-VoIP SMS verification and phone number provider via Browser Use CLI 3.0. Provides one-time SMS verifications and long-term phone number rentals backed by real cellular SIM cards across 100+ countries.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site smspool.net --profile adithya --url https://www.smspool.net/order
```

## Top-Level Routes
- `/order` -> `pages/order.md`
- `/history` -> `pages/history.md`
- `/deposit` -> `pages/deposit.md`
- `/login` -> `pages/login.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Order Temporary SMS Number -> `workflows/order-sms.md`
- Retrieve SMS OTP Verification Code -> `workflows/read-otp.md`
- Cancel Order & Auto-Refund -> `workflows/cancel-refund.md`

## Human Boundaries
Do not bypass security challenges, Cloudflare Turnstile checkpoints, or 2FA prompts without notifying the operator. Do not deposit funds or submit crypto/fiat transactions without explicit user approval.
