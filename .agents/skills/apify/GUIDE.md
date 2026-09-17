# Apify Local Skill User Guide

Deterministic CLI for Apify REST API execution, actor automation, and reverse people/phone lookups.

## Capabilities

- **`apify status`**: Check account readiness, subscription plan, monthly USD usage vs budget, and token validation.
- **`apify run <actor_id>`**: Execute arbitrary Apify actors synchronously with custom JSON input and extract dataset records directly.
- **`apify people-search`**: Dedicated reverse lookup tool wrapping TruePeopleSearch with fallback to Skip Trace People Finder. Extracts full name, age, phone numbers, carrier/type, emails, current & past addresses, relatives, and associates.

---

## Authentication & Tokens

The Apify CLI automatically resolves the token in the following order:
1. `APIFY_TOKEN` environment variable
2. `~/.local/bin/env`
3. Bitwarden item `Apify` custom field `token`

To verify active credentials:
```bash
apify status
```

---

## Common Commands

### 1. Account Status
```bash
apify status
apify status --json
```

### 2. Reverse People & Phone Search

#### Reverse Phone Lookup
```bash
# Look up owner, carrier/type, address, relatives by 10-digit phone number
apify people-search --phone 5167817770
apify people-search --phone "516-781-7770" --json
```

#### Name & Location Lookup
```bash
# Look up person by full name and state
apify people-search --name "John Smith" --state NY --city "Wantagh"
```

#### Reverse Address Search
```bash
# Look up residents by property address
apify people-search --address "123 Main St" --city "Austin" --state TX
```

### 3. Generic Actor Execution
```bash
# Run an actor synchronously with JSON payload
apify run jungle_synthesizer/truepeoplesearch-people-search-scraper \
  --input '{"searchMode":"phone","phone":"5167817770","maxItems":1}'

# Run with input file and save results to file
apify run apivault_labs/skip-trace-people-finder \
  --input @input.json \
  --output results.json
```
