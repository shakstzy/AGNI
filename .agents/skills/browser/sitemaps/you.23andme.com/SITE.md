# you.23andme.com

23andMe genetics customer portal for raw genomic SNP data (.txt.zip) and health predisposition reports.

## Authentication

- **Type**: Form login (email + password) with email OTP or 2FA authenticator app.
- **Login URL**: `https://you.23andme.com/login/`
- **Session Duration**: Persistent sessions survive between automated pulls.
- **Profile Location**: `profiles/adithya/`

## Key URLs

| Page | URL | Purpose |
|------|-----|---------|
| Login | `https://you.23andme.com/login/` | Secure credentials entry |
| Dashboard | `https://you.23andme.com/` | Health & Ancestry summary |
| Browse Raw Data | `https://you.23andme.com/tools/data/` | Search individual SNPs |
| Download Raw Data | `https://you.23andme.com/tools/data/download/` | Request / download full raw data (.txt.zip) |
| Health Predispositions | `https://you.23andme.com/reports/health_predispositions/` | Genetic health risk reports |
| Carrier Status | `https://you.23andme.com/reports/carrier_status/` | Inherited condition carrier reports |

## Workflows

- `workflows/download-raw-genetic-data.md`: Request and download raw genetic SNP zip file.
- `workflows/export-health-reports.md`: Extract health predisposition and carrier status summaries.
