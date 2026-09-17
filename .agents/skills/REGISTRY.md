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

## Local CLI adapters

| Skill | Binary | Handles | Notes |
| --- | --- | --- | --- |
| alpaca | `alpaca.py` | Alpaca Markets portfolio/orders/bars/news | ported script |
| apify | `apify` + `apify.py` | Apify actors, datasets, people search | npm CLI + REST adapter |
| apple-notes | `notes.py` | Notes.app search/create/read | personal Mac SSH |
| apple-reminders | `reminders.py` | Reminders.app lists/tasks | personal Mac SSH |
| article-shot | `article-shot` | Retina article/paper screenshots | external binary — not installed |
| beautiful | `beautiful` | Beautiful.ai decks via MCPorter | ported wrapper |
| blender | `mcporter blender` | BlenderMCP 3D scenes/pipeline | via mcporter |
| bluebubbles | `bluebubbles.py` | iMessage chats/messages/media | ported script |
| catt | `catt` | Chromecast discovery/cast/control | pipx-installed |
| ctx7 | `ctx7` | Context7 live docs lookup | npm-installed |
| expo | `npx expo` | React Native/EAS builds | npx |
| facebook-marketplace | `fbm` | Marketplace listings/search/monitors | ported wrapper |
| firecrawl | `firecrawl` | Web → Markdown scraping | npm-installed |
| goclone | `goclone` | Website mirroring | external binary — not installed |
| google-trends | `trends.py` | Trends velocity/breakouts | ported script |
| granola | `granola` | Meeting notes/transcripts | external binary — not installed |
| home-assistant | `home_assistant.py` | HA REST entities/services | ported script |
| macos | `macos.py` | Remote mac exec/xcodebuild | pinned SSH |
| macos-contacts | `contacts.py` | Contacts.app queries | ported script |
| mcporter | `mcporter` | MCP server mgmt + CLI gen | npm-installed |
| msg | `msg.py` | Unified messaging router | ported script |
| notion | `ntn` | Notion workspaces/pages | external binary — not installed |
| pexels | `pexels.py` | Stock photos/B-roll | PEXELS_API_KEY |
| plaid | `plaid` | Bank balances/liabilities/holdings | external binary — not installed |
| postiz | `postiz` | Social scheduling | npm-installed |
| real-estate | `re` + `scripts/` | Redfin/Zillow, FMR, DSCR, offers | ported wrapper |
| telegram | `telegram` | Chats/messages/contacts | external binary — not installed |
| whatsapp | `wacli` | WhatsApp sync/chats/send | external binary — not installed |
| whisper-at | `tagger.py` | Speech STT + audio event tags | ported script |
| x-cockpit | `x-cockpit` | X virality mining/clustering | external binary — not installed |

## Auxiliary maps

- Android app adapters: `android/adapters/REGISTRY.md`
- Browser sitemap catalog: `browser/sitemaps/REGISTRY.md`
- Harness routing table: `./agni --routes`
