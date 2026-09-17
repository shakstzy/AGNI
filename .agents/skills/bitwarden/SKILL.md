---
name: bitwarden
description: Authenticate and use the Bitwarden CLI (`bw`) on this machine — login, new-device OTP flow, vault unlock, and in-process credential retrieval for the AGNI harness.
---

# Bitwarden CLI — Local Auth & Usage

`bw` is installed via Homebrew (`brew install bitwarden-cli`) and **already
authenticated** on this machine for the account's vault (~380 items). Verified
2026-09-17: `bw status` → `unlocked`.

## Secrets (Devin-managed, user scope)

- `BW_EMAIL` — Bitwarden account login email
- `BW_PASSWORD` — master password
- `BW_CLIENT_ID` / `BW_CLIENT_SECRET` — optional API key (preferred for CI;
  `bw login --apikey` skips new-device OTP)

## Login flow (what actually works)

1. `bw login "$BW_EMAIL" --passwordenv BW_PASSWORD` — non-interactive
   email+password auth.
2. **New-device verification**: Bitwarden emails an OTP to the login email
   *on every `bw login` attempt*. Each new attempt generates a **new code and
   invalidates the previous one** — so piping a previously-sent code via stdin
   always fails (`invalid new device otp`).
3. The only reliable non-interactive path: start `bw login` in a live
   process, have the user read the OTP from the freshest email, and type it
   into that same prompt. Do NOT retry `bw login` before the user sends the
   code — the retry sends a different code.
4. `bw login --apikey` with `BW_CLIENT_ID`/`BW_CLIENT_SECRET` avoids the OTP
   entirely — prefer it when the API key is provisioned.

## Unlock

```bash
export BW_SESSION="$(bw unlock --raw --passwordenv BW_PASSWORD)"
bw status   # -> "unlocked"
```

## Credential retrieval — zero secret exposure

- Consume credentials **in-process**; never dump `bw get item` JSON to stdout
  or files (it contains the raw password).
- AGNI does this for you: `auth(action=load, site=<item>)` pulls
  username/password/TOTP into `AGNI_LOGIN_*` env vars; the `browser` tool with
  `use_login_env=true` injects them into `browser-use` — secrets never enter
  the transcript.
- Standalone equivalent:
  ```bash
  bw get username "<item>"   # field-level reads print less than full JSON
  bw get totp "<item>"
  ```
- `bw sync` before reads if items look stale.

## Boundaries

- `bw delete`, org/user management, and anything printing vault secrets to
  logs require explicit human approval (enforced by AGNI guards).
- Never commit `data.json`, sessions, or item exports — the CLI state lives
  in `~/Library/Application Support/Bitwarden CLI/`.
