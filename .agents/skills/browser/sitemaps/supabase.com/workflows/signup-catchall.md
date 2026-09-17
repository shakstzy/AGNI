# Workflow: Supabase Sign-Up via Catch-All Email

Automated procedure for provisioning and confirming a Supabase cloud account using the `@outerscope.xyz` catch-all email mechanism.

## Prerequisites

1. Active Google Workspace catch-all routing on `outerscope.xyz` pointing to `operations@outerscope.xyz`.
2. Verified `gog` CLI authentication for `operations@outerscope.xyz`.
3. Dedicated profile configuration under `profiles/supabase-03/` (CDP port 9322).

## Procedure

1. **Launch Browser Profile**:
   Launch Chrome on isolated port 9322 targeting `https://supabase.com/dashboard/sign-up`.

2. **Submit Registration**:
   - Fill `input[name="email"]` with `supabase-03@outerscope.xyz`.
   - Fill `input[name="password"]` with the secure password.
   - Click the "Sign up" button.

3. **Harvest Confirmation Link**:
   Poll `operations@outerscope.xyz` using the HADES Catch-All manager:
   ```bash
   python3 workspaces/auth/catchall.py extract-url --alias supabase-03@outerscope.xyz --timeout 90
   ```

4. **Confirm Account**:
   Navigate the active browser session to the harvested confirmation URL (`https://auth.supabase.io/auth/v1/verify?...`).

5. **Verify Authentication**:
   Confirm navigation completes to `https://supabase.com/dashboard/projects` or `/dashboard/new`.
