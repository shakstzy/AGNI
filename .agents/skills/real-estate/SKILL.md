---
name: real-estate
description: Real estate CLI for property lookups, Redfin & Zillow data extraction, school ratings, HOA fees, property taxes, rental estimates, and cash flow analysis.
---

# Real Estate CLI Guide

Deterministic real estate scraping and research CLI (`re`) interfacing directly with Redfin and Zillow without browser automation or paid API keys.

## Commands

### Address Lookup
```bash
# Side-by-side Redfin + Zillow lookup with aggregate metrics
re lookup "1500 Marshall Ln, Austin, TX 78703"

# Aggregate summary only (beds, baths, sqft, taxes, HOA, schools)
re lookup "1500 Marshall Ln, Austin, TX 78703" --aggregate-only

# Include full raw payloads for downstream mapping
re lookup "1500 Marshall Ln, Austin, TX 78703" --include-raw
```

### Redfin Property & Search
```bash
# Direct Redfin property URL inspection
re redfin property "https://www.redfin.com/TX/Austin/.../home/<id>"

# Search homes in a target market
re redfin search "Austin, TX" --max-price 1500000 --min-beds 3 --num-homes 25

# Redfin price and sale history
re redfin history "<redfin-url>"

# Redfin comparable listings
re redfin comps "<redfin-url>"
```

### Zillow Property & Search
```bash
# Search Zillow by zip code or city
re zillow search "78703" --max-price 2000000 --min-beds 4

# Direct Zillow homedetails URL
re zillow property "https://www.zillow.com/homedetails/.../<zpid>_zpid/"
```

### Rental & Cashflow Modeling
```bash
# Rent estimate triangulation
re rent-estimate "1500 Marshall Ln, Austin, TX 78703"

# Pro-forma investment cash flow analysis
re cashflow "1500 Marshall Ln, Austin, TX 78703" --rate 0.065 --down-pct 0.20

# HUD FY2026 Small Area FMR (SAFMR) lookup
re fmr 44105

# Section 8 voucher economics & utility allowances
re section8 44105 --units 2 --beds-per-unit 3 --rent-per-unit 1250

# Institutional Non-QM DSCR loan underwriting
re dscr --price 120000 --rent 2200 --taxes 2400 --insurance 1200

# Parcel cadastral enrichment (APN, lot, flood, zoning, post-sale tax shock)
re parcel "1234 E 55th St, Cleveland, OH 44103" --price 95000
```

### Capital Allocation & Recommendations
```bash
# Recommend best deals maximizing every dollar spent on a sliding budget
re recommend cleveland --budget 35000

# Include custom stretch capital window (identifies asymmetric higher-return deals)
re recommend cleveland --budget 40000 --stretch 25000

# Machine-readable recommendation output
re recommend cleveland --budget 35000 --json
```
