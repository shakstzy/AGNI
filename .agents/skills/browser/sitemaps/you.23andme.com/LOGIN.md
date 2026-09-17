# 23andMe Authentication Reference

## Login Form
- URL: `https://you.23andme.com/login/`
- Username: Email address (`input[type="email"]` or `input[name="email"]`)
- Password: Password field (`input[type="password"]` or `input[name="password"]`)
- Submit: `button[type="submit"]`

## Two-Factor Authentication
- 23andMe prompts for a 6-digit TOTP code or sends a verification link to email.
- Halt and alert Adithya if OTP is requested unless configured in Bitwarden.
