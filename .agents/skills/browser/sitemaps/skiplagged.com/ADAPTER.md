---
name: skiplagged
site: skiplagged.com
driver: Browser Use CLI 3.0
profile: adithya
---

# Skiplagged Browser Adapter

## Purpose
Autonomous flight search, hidden-city routing, airfare deal discovery, and airline booking handoff via Skiplagged.

## Automation Standard
Automated through Browser Use CLI 3.0 via dedicated Chrome CDP port isolation:
```bash
./.agents/skills/browser/cli/browser opencli --site skiplagged.com --profile adithya --url https://skiplagged.com
```

## Key Capabilities & Workflows
- **Flight & Route Discovery**: Deep-link queries by route, dates, and flexible origin/destination (`SITE.md`).
- **Hidden-City Analysis**: Inspect itineraries with intermediate hidden stops that offer significant savings over direct routes.
- **Deal Scanning**: Real-time extraction of extreme airfare discounts, flight glitches, and price drop feeds.
- **Booking Handoff**: Deep-linking from Skiplagged into partner airlines (American Airlines, United, Delta, etc.) or in-engine checkout.
- **Profile Persistence**: Stateful Chrome session stored under `/home/shakstzy/HADES/.agents/skills/browser/sitemaps/skiplagged.com/profiles/adithya/user_data`.

## Boundaries & Human Intervention
- **Stop at Payment / Checkout**: Always halt and present the final confirmation summary to Adithya before submitting credit card information or finalizing a ticket purchase.
- **Hidden-City Luggage Policy**: Clearly warn when booking a hidden-city route that only carry-on baggage is permitted (checked bags are forwarded to the final scheduled ticket destination).
- **CAPTCHA & Challenges**: Stop immediately on Cloudflare Turnstile, CAPTCHA, or email verification challenges.
- **Zero Secret Exposure**: Never log, print, or leak Bitwarden passwords, session cookies, or OTP codes into chat or transcripts.
