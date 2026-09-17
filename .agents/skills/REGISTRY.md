# Skills Registry

Capability index for AGNI.

| Skill | Path | Handles | Route |
| --- | --- | --- | --- |
| auth | `auth/` | Credentials, 2FA, logins, session verification. Encloses bitwarden + auth2fa emulator. | `auth/SKILL.md` |
| bitwarden | `auth/bitwarden/` | `bw` vault login/OTP/unlock, credential retrieval. | `auth/bitwarden/SKILL.md` |
| browser | `browser/` | browser-use CLI, single shared Chrome profile, 79 sitemaps. | `browser/SKILL.md` |
| gog | `gog/` | Google Workspace: Gmail/Calendar/Drive/Sheets/Tasks. | `gog/SKILL.md` |
| android | `android/` | adb + emulator + UIAutomator; app adapters. | `android/SKILL.md` |
| ios | `ios/` | `xcrun simctl` simulator control. | `ios/SKILL.md` |
| apple | `apple/` | Apple Account / iCloud on this Mac — Contacts, Messages, iCloud dataclasses. | `apple/SKILL.md` |
| scheduler | `scheduler/` | Cron-backed recurring jobs (`workspaces/scheduler/schedule`). | `scheduler/SKILL.md` |

## Auxiliary maps

- Android app adapters: `android/adapters/REGISTRY.md`
- Browser sitemap catalog: `browser/sitemaps/REGISTRY.md`
- Harness routing table: `./agni --routes`
