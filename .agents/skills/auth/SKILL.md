---
name: auth
description: Unified authentication authority — Bitwarden vault credentials, 2FA code generation (bw totp / oathtool / auth2fa Android emulator), and login + session verification. Encloses the bitwarden skill.
---

# Auth — Unified Identity & 2FA Authority

AGNI's single entry point for credentials, 2FA, and logins. Three layers,
resolved in order:

## 1. Credentials — Bitwarden (`bw`)

Vault is authenticated on this machine (see `auth/bitwarden/SKILL.md` for the
full login/OTP/unlock contract). `bw status` → `unlocked`, ~380 items.

- In the agent loop use the `auth` tool: `auth(load, site=<item>)` loads
  username/password/TOTP into `AGNI_LOGIN_*` env; `browser(use_login_env=true)`
  consumes them. Secrets never enter the transcript.
- Standalone: `bw get username|password|totp "<item>"` — prefer field-level
  reads; `bw get item` dumps the raw password.

## 2. 2FA codes — resolution order

1. `bw get totp "<item>"` — seed stored in the vault (majority case).
2. `oathtool -b --totp "<base32-seed>"` — for TOTP seeds kept outside the
   vault. Seeds themselves live in Bitwarden `custom fields` or a dedicated
   `TOTP: <service>` item; never in files or logs.
3. `auth2fa` Android emulator — dedicated virtual device for authenticator
   apps whose secrets can't be exported (hardware-bound, QR-enrolled apps).
   See "Android 2FA emulator" below.

## 3. Android 2FA emulator (`auth2fa`)

A dedicated AVD exists for authenticator-app 2FA: `auth2fa`
(Android 34, google_apis, arm64, pixel_6).

```bash
export ANDROID_SDK_ROOT=/opt/homebrew/share/android-commandlinetools
emulator -avd auth2fa -feature -HVF -accel off -no-window \
         -no-audio -gpu swiftshader_indirect   # headless boot
adb wait-for-device && adb shell getprop sys.boot_completed
```

- **IMPORTANT**: this VM has `kern.hv_support=0` — no Hypervisor.framework.
  Always pass `-feature -HVF -accel off` (TCG software emulation — `-accel off`
  alone still attempts HVF and dies). Boot is slow (minutes); start it before
  you need codes.
- Drive it with the `android` skill / `adb` tools: install the authenticator
  APK, enroll via QR screenshot (`adb exec-out screencap`), read codes via
  `uiautomator dump`.
- Approval boundary: 2FA confirmations and passkey prompts on the emulator
  still require human go-ahead per the HADES contract.

## Session verification

After any login: verify the authenticated state, not the click — check for a
post-login element/URL via the browser sitemap's postcondition, or
`adb shell dumpsys` / `uiautomator dump` for the expected screen. Report the
evidence (selector, URL, or screen text), never "should be logged in".
