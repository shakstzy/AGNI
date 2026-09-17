# Workflow: Authenticate to DistroKid

1. Open profile `adithya` on `distrokid.com`:
   ```bash
   browser opencli --site distrokid.com --profile adithya --url https://distrokid.com/signin/
   ```
2. Click Google SSO button `button[data-testid="google-sso-sign-in-button"]`.
3. In Google OAuth window, authenticate with account `adithyashak@gmail.com`.
4. Checkpoint on any 2FA or passkey challenge.
5. Verify redirection to `https://distrokid.com/mymusic/`.
