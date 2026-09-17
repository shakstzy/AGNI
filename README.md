# AGNI

Routed multi-system agent harness. One LLM tool loop dispatching to ~20
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

`./agni --routes` prints this table; `./agni --doctor` reports binary +
auth status per subsystem.

## Skills & workspaces

- `.agents/skills/` — `auth` (encloses `bitwarden`), `browser` (79 sitemaps,
  single shared Chrome profile), `gog`, `android`, `ios`, `scheduler`.
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
