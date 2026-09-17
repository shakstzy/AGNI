# Google Photos Authentication Guide

Operating procedure for authenticating the persistent browser profile for Google Photos.

## Initial Setup & Interactive Login

Because Google enforces strict device verification, passkeys, and potential 2FA prompts:

1. **Launch Interactive Chrome Session**:
   ```bash
   ./.agents/skills/browser/cli/browser opencli --site photos.google.com --profile adithya --headed --url https://photos.google.com
   ```
2. **User Sign-In**:
   The operator signs into their Google account.
3. **Session Persistence**:
   Google credentials, cookies, and local storage are saved directly into `/home/shakstzy/HADES/.agents/skills/browser/sitemaps/photos.google.com/profiles/adithya/user_data`.
4. Subsequent automations run headlessly or headed using the same profile directory.
