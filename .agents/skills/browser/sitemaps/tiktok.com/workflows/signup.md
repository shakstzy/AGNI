# Workflow: TikTok Account Registration via Email

## Goal
Attempt account registration on tiktok.com using the dedicated `creator` browser profile and `@outerscope.xyz` email catch-all OTP.

## Verified Action Sequence
1. Launch dedicated profile `creator` on CDP port 9350:
   ```bash
   .agents/skills/browser/cli/browser opencli --site tiktok.com --profile creator --url https://www.tiktok.com/signup
   ```
2. Navigate to email registration subpath:
   - Click "Use phone or email" (`/signup/phone-or-email/phone`)
   - Click "Sign up with email" (`/signup/phone-or-email/email`)
3. Set Date of Birth:
   - Click `[aria-label*='Month']` and select month from `[role='option']`.
   - Click `[aria-label*='Day']` and select day from `[role='option']`.
   - Click `[aria-label*='Year']` and select year from `[role='option']`.
4. Populate Credentials:
   - Dispatch value to `input[name='email']` (e.g. `creator@outerscope.xyz` or generated alias).
   - Dispatch 16+ char complex password to `input[type='password']`.
5. Trigger Email Verification:
   - Click `button[data-e2e='send-code-button']`.
   - **Check for Block / Rate Limit**: If TikTok returns `Maximum number of attempts reached. Try again later.`, the web browser IP/client is flagged by ByteDance security SDK.
   - Stop and route to Android native adapter:
     ```bash
     node .agents/skills/android/adapters/tiktok/cli/tiktok.mjs sign-up --email creator@outerscope.xyz
     ```
6. If OTP is sent:
   - Retrieve 6-digit code via `workspaces/auth/catchall.py poll --alias creator --query tiktok`.
   - Enter code into `input[placeholder*='code']`.
   - Click `button[type='submit']`.
