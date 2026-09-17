# Cal.com Authentication Standard

## Identity Reference
- Email: `adithya@outerscope.xyz`
- Provider: Google OAuth (`accounts.google.com`)
- Vault Lookup: `accounts.google.com (adithya@outerscope.xyz)`
- 2FA Strategy: Google prompt verification on connected Android device (Pixel 3).

## Auth Strategy
1. Click "Sign in with Google" / "Sign up with Google".
2. Submit `adithya@outerscope.xyz` and password from Bitwarden.
3. If Google requests on-device 2FA approval, confirm on Android.
4. Grant Google Calendar read/write access to sync events.
