# Page: Sign Up (TikTok)

## Path
`/signup/phone-or-email/email`

## Purpose
TikTok account registration form using email and password with birthday verification and email OTP.

## Semantic Anchors
- **birthday_month**: `[aria-label*='Month']`
- **email_input**: `input[name='email']`
- **password_input**: `input[type='password']`
- **send_code_btn**: `button[data-e2e='send-code-button']`

## Key Elements
- **birthday_month**: Month Dropdown (`[aria-label*='Month']`, options role `option`)
- **birthday_day**: Day Dropdown (`[aria-label*='Day']`, options role `option`)
- **birthday_year**: Year Dropdown (`[aria-label*='Year']`, options role `option`)
- **email_input**: Email Address Input (`input[name='email']`)
- **password_input**: Password Input (`input[type='password']`)
- **code_input**: Verification Code Input (`input[placeholder*='code']`)
- **send_code_btn**: Request OTP Button (`button[data-e2e='send-code-button']`)
- **submit_btn**: Submit Registration (`button[type='submit']`)

## Anti-Bot & Boundary Rules
- Web registration is actively guarded by ByteDance security SDK (`X-Bogus`, `verifyFp`, `SLARDAR`).
- Automated headless or desktop CDP requests to `/passport/web/email/send_code/` may fail with `Maximum number of attempts reached. Try again later.`.
- When web registration is blocked by security thresholds, route to the Android app adapter (`.agents/skills/android/adapters/tiktok/`) for mobile device registration.
