# Cal.com Browser Adapter

## Standard Operations
1. Launch profile:
   ```bash
   .agents/skills/browser/cli/browser opencli --site cal.com --profile adithya --url https://cal.com/signup
   ```
2. Authenticate using Google OAuth (`adithya@outerscope.xyz`).
3. Handle 2FA on Android device via `.agents/skills/android/cli/android.mjs`.
