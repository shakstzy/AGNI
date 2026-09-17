# Workflow: Booking Handoff (Skiplagged)

## Goal
Transition from an identified Skiplagged itinerary to the direct airline booking portal or merchant checkout with stored credentials.

## Verified Action Sequence
1. Select the desired itinerary card on Skiplagged.
2. Click "Select" or "Book" to reveal booking provider options (Airline direct vs OTA).
3. Identify operating carrier (e.g. American Airlines, United, Delta, Southwest).
4. If the airline matches a configured browser sitemap (`aa.com`, `united.com`), switch to the airline profile or open deep link with authenticated session.
5. Autofill passenger identity from Bitwarden (`VADER traveler identity — Adithya`).
6. STOP strictly before credit card submission or final payment click. Present booking summary for operator confirmation.
