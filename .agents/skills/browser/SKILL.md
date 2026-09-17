---
name: browser
description: Rendered web automation via the browser-use CLI, a single shared Chrome profile, and HADES-ported per-site sitemaps.
---

# Browser Skill

Rendered web automation owned by **browser-use CLI 0.1.x** against **one
shared Chrome profile** — AGNI uses a single `default` profile for all sites
to avoid session fragmentation.

## Single profile

- Metadata: `profiles/default/metadata.json` — `user_data/` (git-ignored),
  CDP port `9222`, session id `agni-default`.
- Launch:
  ```bash
  python3 launch_profile.py profiles/default/metadata.json --url <url>
  export BU_CDP_URL="http://127.0.0.1:9222"
  ```
- Logins persist per-site inside the shared `user_data/` — authenticate once
  (via the `auth` skill), reuse everywhere.

## Driving the browser

browser-use is a heredoc REPL over a daemon; helpers are pre-imported:

```bash
browser-use <<'PY'
ensure_real_tab()
print(page_info())
PY
```

- `browser-use --doctor` — diagnose daemon/browser state.
- `BU_NAME=<job>` isolates daemon sessions per job (tab-per-job isolation).

## Sitemaps

`sitemaps/<host>/` — 79 site specs ported from HADES:
- `sitemap.json` — semantic selectors + postconditions
- `SITE.md`, `LOGIN.md` — navigation/auth notes
- `pages/`, `workflows/` — page elements and goal flows

Consult the sitemap before interacting with a known host; verify its stated
postcondition after the action. Per-site `profiles/` dirs were intentionally
NOT ported — everything uses `profiles/default/`.

## Boundaries

- Stop at unresolved MFA/passkeys — route 2FA through the `auth` skill, or
  escalate to a human for biometric/push approvals.
- Purchases, transfers, and financial mutations are REFUSED by harness guards.
- Never log passwords, cookies, or OTP codes; daemon cleanup on job exit.
