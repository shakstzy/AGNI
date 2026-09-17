# DistroKid Browser Adapter

Browser Use CLI 3.0 automation adapter for DistroKid music management and distribution.

## Purpose

Automates single and album releases on DistroKid, catalog verification, and store release monitoring for Shak STZY / Outerscope Records.

## Execution Standards

- **CLI Access**:
  ```bash
  browser opencli --site distrokid.com --profile adithya [--headless|--headed]
  ```
- **Port Assignment**: `9333`
- **Data Directory**: `.agents/skills/browser/sitemaps/distrokid.com/profiles/adithya/user_data`

## Human Boundaries & Checkpoints

- **Final Submission Confirmation**: In live releases, dry-run upload parameters first. The final submit click initiates global DSP ingestion.
- **2FA & Captchas**: If Google or DistroKid challenges with biometric passkey, SMS, or Recaptcha, pause and request user confirmation.
- **Artwork Strict Specs**: 3000 x 3000 px RGB JPEG required. DistroKid will reject smaller or non-square assets before file upload starts.

## Workflows

1. `workflows/login.md`: Authenticate using Google SSO (`adithyashak@gmail.com`).
2. `workflows/list-releases.md`: Query all published and in-review albums from `/mymusic/`.
3. `workflows/upload.md`: Stage artwork, audio WAV, and metadata on `/new/`.
