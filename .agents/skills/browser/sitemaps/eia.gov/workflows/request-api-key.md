# Request API Key Workflow

1. Navigate to `https://www.eia.gov/opendata/register.php`.
2. Fill `#firstName` with "Adithya", `#lastName` with "Kumar".
3. Fill `#email` with "adithya@outerscope.xyz".
4. Check `#tos` (agree to terms of service).
5. Click `input[name='Register']`.
6. Retrieve verification email from Gmail using `gog gmail messages search "EIA"`.
7. Extract the verification URL and submit HTTP request to activate key.
8. Store the delivered API key into Bitwarden item `HADES Trading - EIA Open Data API`.
