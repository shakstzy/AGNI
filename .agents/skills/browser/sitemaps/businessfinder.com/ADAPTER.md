---
name: businessfinder
site: businessfinder.com
driver: Browser Use CLI 3.0
profile: adithya
---

# BusinessFinder Browser Adapter

## Purpose
Direct scraping, extraction, and automated inquiry workflow for business acquisition opportunities, owner-operator listings, and broker contacts on BusinessFinder.

## Automation Standard
Automated through Browser Use CLI 3.0 via dedicated Chrome CDP port isolation:
```bash
./.agents/skills/browser/cli/browser opencli --site businessfinder.com --profile adithya --url https://www.businessfinder.com/search
```

## Key Capabilities & Workflows
- **Search & Discovery**: Query by industry (e.g., laundromat, HVAC, roofing, car wash, plumbing), state/city (e.g., Texas, Austin, DFW), and price/cash flow ranges (`workflows/search-listings.md`).
- **Inspection & Parsing**: Extract structured attributes including asking price, reported gross revenue, reported cash flow / SDE, owner involvement status, lease details, and broker/seller contacts (`workflows/extract-listing-card.md`).
- **Profile Persistence**: Stateful Chrome session stored under `/home/shakstzy/HADES/.agents/skills/browser/sitemaps/businessfinder.com/profiles/adithya/user_data`.

## Boundaries & Human Intervention
- Stop immediately on CAPTCHA, Cloudflare Turnstile challenges, or SMS/phone verification.
- Never log, export, or leak Bitwarden secrets or session cookies into chat or transcripts.
- Stop before unauthorized state mutations, credit card payments, or binding legal commitments.
