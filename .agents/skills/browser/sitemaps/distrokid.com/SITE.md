# DistroKid Sitemap Guide (distrokid.com)

High-level navigation, identity, and operational procedures for DistroKid music distribution.

## Purpose & Scope

DistroKid distributes audio tracks, singles, and albums to Spotify, Apple Music, TikTok, Amazon Music, and all global DSPs. This sitemap automates catalog inspection, track release uploads, artwork verification, and metadata ingestion.

## Standard Routes

| Route | Purpose | Key Verification Anchors |
| --- | --- | --- |
| `/signin/` | Authentication | `button[data-testid='google-sso-sign-in-button']` |
| `/mymusic/` | Catalog Dashboard | `.releaseItem, a[href*='/new/']` |
| `/new/` | Upload / Release Submission | `#file_art, input[name='file_track1'], #saveAndContinue` |
| `/new/done/` | Submission Confirmation | `h1, [data-album-uuid]` |

## Session & Profile Requirements

- **Profile**: Use profile `adithya` (`profiles/adithya/metadata.json`, CDP port `9333`).
- **Auth Provider**: Google OAuth SSO with `adithyashak@gmail.com`.
- **Artist Metadata**:
  - Artist Name: `Shak STZY`
  - Record Label: `Outerscope Records`
  - Songwriter: `Adithya Shakthi Kumar`

## Automation Driver

Operates via **Browser Use CLI 3.0** (`browser opencli --site distrokid.com --profile adithya`) or direct persistent Chrome context via CDP.
