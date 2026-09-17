# AGNI

Routed multi-system agent harness. One LLM tool loop dispatching to 40+
subsystems on the HADES operating contract: **deterministic CLIs > headless
browser > device UI**, in-process secret handling, and hard refusal
boundaries on irreversible actions.

## Routing

| tool | binary | handles |
|------|--------|---------|
| `auth` | pipeline | `bw` unlock → creds → `browser-use` fill (secrets stay in-process) |
| `bitwarden` | `bw` | vault status/unlock, item search |
| `twofa` | `oathtool` | local TOTP generation (`bw get totp` preferred) |
| `github` | `gh` | repos, PRs, issues, actions, `gh api` |
| `gog` | `gog` | Gmail, Calendar, Drive, Docs, Sheets, Tasks (`--account=<email>`) |
| `browser` | `browser-use` | rendered web automation; `BU_CDP_URL`, `BU_NAME` |
| `android` | `adb` | taps, swipes, text, uiautomator dump, screencap |
| `emulator` | `emulator` | AVD boot — `auth2fa` 2FA device (always `-accel off`) |
| `ios` | `xcrun simctl` | simulator boot/install/launch/screenshot |
| `scheduler` | `workspaces/scheduler/schedule` | cron-backed recurring jobs |
| `stripe` | `stripe` | payments, customers, subscriptions |
| `supabase` | `supabase` | projects, db, functions, deploy |
| `firebase` | `firebase` | projects, hosting, functions, deploy |
| `gcloud` | `gcloud` | compute, run, iam, secrets |
| `docker` | `docker` | build, run, compose, logs |
| `wrangler` | `wrangler` | Cloudflare Workers/Pages/KV/R2/D1 |
| `vercel` | `vercel` | deploys, env, domains, logs |
| `cloudflared` | `cloudflared` | tunnels |
| `rclone` | `rclone` | cloud storage sync |
| `ffmpeg` | `ffmpeg` | media transcode/probe |
| `ytdlp` | `yt-dlp` | media download |
| `exiftool` | `exiftool` | file metadata |
| `apify` | `apify` | scraping actors/datasets |
| `mcporter` | `mcporter` | MCP server mgmt, auth, CLI generation |
| `ctx7` | `ctx7` | live library docs lookup |
| `firecrawl` | `firecrawl` | web → Markdown scraping |
| `postiz` | `postiz` | social media scheduling |
| `catt` | `catt` | Chromecast discovery/cast/control |
| `expo` | `npx expo` | React Native/EAS builds |
| `alpaca` | `alpaca.py` | Alpaca portfolio/orders/bars/news |
| `apple-notes` | `notes.py` | Notes.app on personal Mac |
| `apple-reminders` | `reminders.py` | Reminders.app on personal Mac |
| `bluebubbles` | `bluebubbles.py` | iMessage chats/messages/media |
| `fbm` | `fbm` | Facebook Marketplace |
| `trends` | `trends.py` | Google Trends velocity/breakouts |
| `home-assistant` | `home_assistant.py` | HA entities/services |
| `macos` | `macos.py` | remote mac exec/xcodebuild (SSH) |
| `contacts` | `contacts.py` | Contacts.app queries |
| `msg` | `msg.py` | unified messaging router |
| `re` | `re` | real-estate lookups/DSCR/offers |
| `whisper-at` | `tagger.py` | speech STT + audio event tags |
| `pexels` | `pexels.py` | stock photos/B-roll |
| `beautiful` | `beautiful` | Beautiful.ai decks via MCPorter |
| `blender` | `mcporter blender` | BlenderMCP 3D scenes |

Routed but not yet installed here (external binaries; `./agni --doctor`
flags MISSING): `plaid`, `ntn` (notion), `telegram`, `wacli` (whatsapp),
`goclone`, `article-shot`, `granola`, `x-cockpit`.

`./agni --routes` prints this table; `./agni --doctor` reports binary +
auth status per subsystem.

## Skills & workspaces

- `.agents/skills/` — `auth` (encloses `bitwarden`), `browser` (79 sitemaps,
  single shared Chrome profile), `gog`, `android`, `ios`, `apple`,
  `scheduler`, plus 30+ ported HADES CLI adapters — index in
  `.agents/skills/REGISTRY.md`.
- `workspaces/scheduler/` — `schedule` CLI + `jobs.json`, crontab sync.

## Auth / login flow

```sh
agni auth github --url https://github.com/login
# or in the loop: auth(action=load, site=<bw-item>) then
# browser(argv=[...], use_login_env=true)
```

1. `bw` unlock via `BW_SESSION` or `AGNI_BW_PASSWORD`.
2. `bw get item <site>` consumed **in-process** → `AGNI_LOGIN_*` env vars.
3. `browser` tool runs with those injected (`use_login_env=true`).
4. 2FA: `bw get totp` → `oathtool` → `auth2fa` emulator.

## Requirements

Binaries: `bw gh gog browser-use adb xcrun emulator oathtool stripe supabase
firebase gcloud docker wrangler vercel cloudflared rclone ffmpeg yt-dlp
exiftool apify` — all installed on this machine via Homebrew/npm/uv.
`OPENAI_API_KEY` (or `AGNI_API_KEY`); `AGNI_MODEL`, `AGNI_BASE_URL`,
`AGNI_MAX_TURNS` optional.

## Usage

```sh
./agni "check github notifications and summarize today's calendar"
./agni "log into example.com and screenshot the dashboard"
./agni auth <bitwarden-item> [--url <login_url>]
./agni --dry-run "triage unread gmail"   # print tool calls, don't execute
./agni --doctor && ./agni --routes
```
