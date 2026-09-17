# Page: Order (SMSPool)

## Path
`/order`

## Purpose
Order one-time temporary SMS verification numbers across global countries and specific online services (Tinder, Google, OpenAI, Telegram, WhatsApp, etc.).

## Semantic Anchors
  - **country_select**: `#country`
  - **service_select**: `#service`
  - **quick_order_button**: `button:has-text('Quick Order')`
  - **pricing_display**: `.pricing`

## Key Elements
  - **country_picker**: Country Selection Dropdown (`#country`)
  - **service_picker**: Service Selection Dropdown (`#service`)
  - **order_btn**: Quick Order Button (`button[type='submit']`)
  - **active_number**: Allocated Phone Number (`.phone-number`)
