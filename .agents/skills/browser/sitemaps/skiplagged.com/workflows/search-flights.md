# Workflow: Search Flights (Skiplagged)

## Goal
Search and compare standard and hidden-city flight routes on skiplagged.com using Browser Use CLI 3.0.

## Verified Action Sequence
1. Attach to Skiplagged session on CDP port 9358:
   ```bash
   ./.agents/skills/browser/cli/browser opencli --site skiplagged.com --profile adithya --url https://skiplagged.com
   ```
2. Navigate directly to targeted flight route URL, e.g.:
   `https://skiplagged.com/flights/{origin}/{destination}/{date}`
3. Wait for the flight results container to populate.
4. Extract the lowest fare, non-stop options, and any hidden-city itineraries with savings.
5. If hidden-city is selected, note the true destination airport and inform the user of carry-on luggage rules.
