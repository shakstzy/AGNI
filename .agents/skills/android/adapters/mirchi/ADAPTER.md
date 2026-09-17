# Mirchi Android Adapter


Then read the generic Android skill.

This adapter binds only the verified package `com.dating.mirchi`. It exposes
fresh initial-surface checks plus the observed phone-login navigation, fill,
and explicit code-request actions. No provider handoff was observed.

## Commands

```bash
node .agents/skills/android/adapters/mirchi/cli/mirchi.mjs check
node .agents/skills/android/adapters/mirchi/cli/mirchi.mjs open
node .agents/skills/android/adapters/mirchi/cli/mirchi.mjs inspect
node .agents/skills/android/adapters/mirchi/cli/mirchi.mjs screenshot --out initial.png
node .agents/skills/android/adapters/mirchi/cli/mirchi.mjs begin-login --method phone
phone-json-producing-command | node .agents/skills/android/adapters/mirchi/cli/mirchi.mjs fill-phone
node .agents/skills/android/adapters/mirchi/cli/mirchi.mjs request-code --confirm request
```

`check` confirms the exact package. `open` launches it and returns fresh
foreground and UI state. `inspect` returns fresh foreground and UI state.
`screenshot` writes runtime-only output below the ignored Android runtime
directory.

`begin-login --method phone [--serial <device-id>]` accepts no other method.
It launches the verified package, condition-waits for an exact app-owned
phone-form or initial-login anchor, then freshly proves foreground and safety.
It returns ready without a tap when the exact empty phone form is already
shown; otherwise it guarded-taps only `SIGN IN WITH NUMBER`, condition-waits
for the exact phone form, and refreshes it. It does not enter a number or
request a code.

`fill-phone [--serial <device-id>]` reads exactly one JSON object from standard
input with the shape `{ "phone": "..." }`. The phone must be a non-empty,
single-line string. It is never accepted on a command-line option or returned
in output. The command freshly proves the Mirchi foreground and exact phone
form, guarded-taps `com.dating.mirchi:id/etNumber`, refreshes safety state,
types through the generic Android `type-stdin` command, and refreshes again.
It never taps Continue or requests a code.

`request-code --confirm request [--serial <device-id>]` reads no credential.
It requires the exact confirmation, freshly proves the Mirchi foreground and
phone form, guarded-taps only `com.dating.mirchi:id/btnContinue`, and inspects
again. The post-request inspection requires exact Mirchi focus and rejects
every unsafe stop category. A neutral Mirchi-owned code-entry surface may be
reported, but no code is entered. The result reports only that submission was
observed; authentication remains unverified.

Stop before provider or account handoffs, passkeys, 2FA, CAPTCHA, permissions,
purchases, profile setup, social linking, messaging, or engagement. These
commands do not submit a received code and do not claim authentication success.

The redacted selector evidence is recorded in the ignored discovery report at
`.superpowers/sdd/2026-08-10-android-dating-and-store-adapters/task-7-mirchi-login-discovery.md`.
It contains no screenshot, credential, or raw UI dump.
