# Page: Home (Skiplagged)

## Path
`/`

## Purpose
Main search interface for querying flights between origin and destination with flexible dates.

## Semantic Anchors
- **flight_search_box**: `#search-form`
- **origin**: `input#src-input, input[placeholder*='Departing from']`
- **destination**: `input#dst-input, input[placeholder*='Arriving at']`
- **depart_date**: `input#depart-input`
- **search_button**: `button[type='submit']`

## Key Elements
- **origin_input**: Input field for departing 3-letter IATA code or city name.
- **destination_input**: Input field for destination IATA code or "Anywhere".
- **depart_date**: Date picker for departure.
- **search_button**: Button triggering search.
