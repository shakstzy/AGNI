# AGNI

Minimalist, functional autonomous operating architecture — routed agent
harness over local CLIs, browser, and mobile device control.

## Communication

- **Action-first**: lead with the direct action/command. No filler.
- **Brief**: ≤5 items per list, 1–2 sentence paragraphs, bold key tokens.
- **Evidence**: report what was done with verification output; never claim
  success without fresh tool output.

## Execution & Routing

- **Hierarchy**: deterministic CLIs > headless browser > device UI
  (adb/simctl). No discovery loops before routine commands.
- **Direct dispatch**: run CLIs directly via `./agni "<task>"`; consult
  `.agents/skills/<name>/SKILL.md` or sitemaps only when syntax is needed.
- **Zero approval gates** for reversible ops; escalate only truly
  irreversible/destructive actions (harness guards REFUSE these
  automatically: deletes, merges, sends, money movement, passcodes).

## Capabilities

### Skills (`.agents/skills/`)

- `auth` — unified credentials + 2FA: Bitwarden vault (`bw`), `oathtool`
  TOTP, `auth2fa` Android emulator (boot with `-accel off`; no Hypervisor on
  this VM), session verification.
- `browser` — browser-use CLI against **one shared Chrome profile**
  (`profiles/default`, CDP :9222); 79 HADES sitemaps in `sitemaps/<host>/`.
- `gog` — Google Workspace CLI (Gmail/Calendar/Drive/Sheets/Tasks).
- `android` — adb + UIAutomator + helper CLIs; app adapters.
- `ios` — `xcrun simctl` simulator control.
- `scheduler` — cron jobs via `workspaces/scheduler/schedule`.

### Routed CLIs (`./agni --routes`)

`bw`, `gh`, `gog`, `browser-use`, `adb`, `xcrun simctl`, `emulator`,
`oathtool`, `schedule`, `stripe`, `supabase`, `firebase`, `gcloud`, `docker`,
`wrangler`, `vercel`, `cloudflared`, `rclone`, `ffmpeg`, `yt-dlp`,
`exiftool`, `apify` — each with refusal guards on destructive ops.

### Workspaces (`workspaces/<domain>/`)

- `scheduler` — recurring job management.

## Boundaries

- Secrets: consume in-process (bw items → `AGNI_LOGIN_*` env); never print,
  log, or commit credentials, sessions, or OTP codes.
- 2FA: `bw get totp` → `oathtool` → `auth2fa` emulator; passkey/push
  approvals escalate to a human.
- Verification: check postconditions (sitemap, screen state, exit codes)
  before reporting success.
