---
site: businessfinder.com
login_required: false
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# Business Finder Sitemap

## Overview
BusinessFinder directory search, SMB listings discovery, business-for-sale records, and local owner/broker contact parsing via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site businessfinder.com --profile adithya --url https://www.businessfinder.com/search
```

## Top-Level Routes
- `/search` -> `pages/search.md`
- `/listing/:id` -> `pages/listing_detail.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Search SMB Listings -> `workflows/search-listings.md`
- Extract Listing Card & Financials -> `workflows/extract-listing-card.md`
- Submit Acquisition Inquiry -> `workflows/contact-inquiry.md`

## Human Boundaries
Do not bypass bot-detection challenges, Cloudflare turnstile checkpoints, or paid lead unlock paywalls without notifying the operator.
