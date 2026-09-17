---
site: skiplagged.com
login_required: false
driver: Browser Use CLI 3.0
profile_hint: adithya
---

# Skiplagged Sitemap

## Overview
Skiplagged cheap flight finder, hidden-city routing, deals, and airline booking handoff via Browser Use CLI 3.0.

## Browser Use CLI 3.0 Launch
```bash
.agents/skills/browser/cli/browser opencli --site skiplagged.com --profile adithya --url https://skiplagged.com
```

## Top-Level Routes
- `/` -> `pages/home.md`
- `/flights/{from}/{to}/{depart}` -> `pages/flight_results.md`
- `/deals` -> `pages/deals.md`
- Profiles -> `profiles/REGISTRY.md`

## Common Workflows
- Search Cheap & Hidden-City Flights -> `workflows/search-flights.md`
- Scan Deals & Fare Glitches -> `workflows/discover-deals.md`
- Airline Booking Handoff -> `workflows/booking-handoff.md`

## Human Boundaries
Do not submit payments, credit card details, or finalize bookings without explicit user approval. When recommending hidden-city itineraries, explicitly alert the traveler not to check baggage.
