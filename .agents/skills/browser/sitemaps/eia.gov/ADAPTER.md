# EIA Browser Adapter

## Purpose
Automates registration, API key retrieval, and documentation navigation for the U.S. Energy Information Administration (EIA) open data services.

## Browser Use CLI 3.0 Execution
```bash
.agents/skills/browser/cli/browser opencli --site eia.gov --profile adithya --url https://www.eia.gov/opendata/register.php
```

## Human Boundaries
- Stop if CAPTCHA or Cloudflare protection triggers.
- Do not automate paid services (EIA is 100% free federal public data).
