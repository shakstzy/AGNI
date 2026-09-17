# Workflow: Extract Listing Card & Financials

1. Load target listing URL (`https://www.businessfinder.com/listing/:id`).
2. Parse headline title, location text, asking price, gross revenue, and reported SDE.
3. Check for owner-operator signals (e.g. absentee, semi-absentee, full-time).
4. Extract lease tenure and equipment / FF&E valuation notes if present.
5. Identify broker name, brokerage firm, direct phone, and contact email or form endpoint.
6. Transform into normalized Quarry deal schema JSON for the `discover` ledger.
