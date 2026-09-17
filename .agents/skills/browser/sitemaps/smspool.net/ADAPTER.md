---
name: smspool
site: smspool.net
driver: Browser Use CLI 3.0
profile: adithya
---

# SMSPool Browser Adapter

## Purpose
SMSPool temporary non-VoIP SMS verification number provider, real physical SIM cards across 100+ countries, OTP code retrieval, and automated failure refund management.

## Automation Standard
Automated through Browser Use CLI 3.0 via dedicated Chrome CDP port isolation:
```bash
./.agents/skills/browser/cli/browser opencli --site smspool.net --profile adithya --url https://www.smspool.net/order
```

## Key Capabilities & Workflows
- **Navigation**: Direct deep-linking via sitemap routes (`SITE.md`).
- **Inspection**: Semantic element anchors and accessibility roles (`sitemap.json` and `pages/`).
- **Profile Persistence**: Stateful Chrome session stored under `/home/shakstzy/HADES/.agents/skills/browser/sitemaps/smspool.net/profiles/adithya/user_data`.
- **Order SMS Verification**: Select target country and service (e.g., Tinder, OpenAI, Google) and acquire disposable phone number (`workflows/order-sms.md`).
- **Retrieve OTP**: Real-time polling and extraction of verification codes from incoming SMS messages (`workflows/read-otp.md`).
- **Automatic Refund**: Cancel unfulfilled verification orders to instantly credit account balance (`workflows/cancel-refund.md`).

## Boundaries & Human Intervention
- Stop immediately on CAPTCHA, Cloudflare Turnstile, SMS/Email OTP checkpoints, or biometric / passkey prompts.
- Never log, export, or leak Bitwarden secrets, API keys, or session cookies into chat or transcripts.
- Stop before unauthorized state mutations, wallet deposits, or destructive account modifications.
