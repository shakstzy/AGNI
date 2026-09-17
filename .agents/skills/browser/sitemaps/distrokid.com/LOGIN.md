# DistroKid Login Reference

- **Profile**: Use `adithya` profile under `profiles/adithya/` (`profiles/adithya/metadata.json`).
- **Target Account**: `adithyashak@gmail.com`
- **Method**: Google OAuth Single Sign-On via `button[data-testid='google-sso-sign-in-button']`.
- **Vault Reference**: Bitwarden item `accounts.google.com (adithyashak@gmail.com)` or `distrokid.com (adithya.shak.kumar@gmail.com)`.
- **Checkpoint Rule**: Stop on captcha, biometric challenge, or device 2FA prompt. Never attempt brute-force password retries.
