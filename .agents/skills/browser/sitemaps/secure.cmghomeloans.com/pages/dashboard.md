# CMG Home Loans Mortgage Dashboard

- **Route**: `https://secure.cmghomeloans.com/dashboard`
- **Key Elements**:
  - `unpaid_principal_balance`: Current mortgage debt remaining on the property
  - `interest_rate`: Current note rate (e.g. 6.125%)
  - `escrow_balance`: Funds held in escrow for property taxes and homeowner insurance
  - `monthly_payment`: Total monthly payment obligation
  - `payment_due_date`: Calendar date for upcoming payment cycle
- **Data Ingest**:
  - Values extracted from this view feed `workspaces/finance/stages/01_ingest/` for mortgage liability tracking.
