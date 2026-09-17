# Hinge Android Adapter


Then read the generic Android skill.

This adapter binds only the installed package `co.hinge.app`. It exposes fresh
initial-surface checks plus the exact observed phone-login actions below.

## Commands

```bash
node .agents/skills/android/adapters/hinge/cli/hinge.mjs check
node .agents/skills/android/adapters/hinge/cli/hinge.mjs open
node .agents/skills/android/adapters/hinge/cli/hinge.mjs inspect
node .agents/skills/android/adapters/hinge/cli/hinge.mjs screenshot --out initial.png
node .agents/skills/android/adapters/hinge/cli/hinge.mjs begin-login --method phone
phone-json-producing-command | node .agents/skills/android/adapters/hinge/cli/hinge.mjs fill-phone
node .agents/skills/android/adapters/hinge/cli/hinge.mjs request-code --confirm request
```

`check` confirms the package. `open` launches it and returns fresh foreground
and UI state. `inspect` returns fresh foreground and UI state. `screenshot`
writes runtime-only output below the ignored Android runtime directory.

`begin-login --method phone [--serial <device-id>]` first verifies the package
then launches Hinge. It checks the unique exact phone-form title anchor for an
already-resumed empty phone form. Otherwise, it bounded-waits the unique
observed `Sign in with Phone Number` `TextView` with no resource ID, then
freshly proves exact Hinge focus and the full navigation fingerprint at
`[265,1678][815,1732]` before sending it to the generic guarded tap. It
bounded-waits the phone-form title again and freshly proves the exact empty
phone surface. Its redacted result says only that the phone surface is ready
and no code was requested. No Google method is implemented.

`fill-phone [--serial <device-id>]` reads exactly one JSON object from standard
input: `{ "phone": "..." }`. `phone` must be a non-empty, single-line string;
no other field is accepted. The phone is never accepted in a CLI option and is
never returned in JSON, errors, logs, or files. The command freshly proves the
exact Hinge focus and phone surface, guarded-taps the phone field, re-inspects,
passes the phone only through child standard input to the generic Android
`type-stdin` command, and re-inspects again. It never taps Continue or requests
a code. It requires the observed empty field before typing, so it never appends
to a pre-existing phone value.

`request-code --confirm request [--serial <device-id>]` reads no credential or
code and performs no device action without that exact confirmation. It freshly
proves the exact Hinge focus and phone surface, guarded-taps only the observed
Continue button, then freshly proves that Hinge remains foreground and checks
the next surface for unsafe handoffs. A neutral Hinge code-entry surface may be
observed, but there is no code-entry action. Its result says only
`submission-observed` and `authentication: unverified`; it does not claim that
a code was sent or that authentication succeeded.

The exact observed phone surface is:

- heading `What's your phone number?`, no resource ID, `TextView`, `[94,209][986,414]`
- one no-ID `EditText` phone field, `[460,691][1025,856]`
- nested `Continue` `TextView`, no resource ID, `[448,1761][633,1813]`
- one unlabeled, no-ID `Button` containing Continue, `[375,1722][705,1852]`
- disclosure `Hinge will send you a text with a verification code. Message and data rates may apply.`, no resource ID, `TextView`, `[44,1907][1036,1973]`

The redacted selector evidence is recorded in
`.superpowers/sdd/2026-08-10-android-dating-and-store-adapters/task-7-hinge-login-discovery.md`.
No raw UI dump or screenshot is retained.

Every mutation uses an immediately observed index, exact empty resource ID,
class, exact non-zero bounds, proven text/content description where available,
and `--unique true`. The generic Android command takes its own fresh dump and
refuses a missing, moved, changed, or duplicate final fingerprint or any
visible defined unsafe surface before the tap.

The phone actions fail closed before their next mutation when focus is not the
exact Hinge package, an observed surface or control is missing, moved, changed,
or duplicated, or a provider/account handoff, passkey/identity, 2FA, CAPTCHA,
permission, purchase, profile, or social surface is visible. Stop there and
hand control to Adithya. There is no code-entry action and no Google-provider,
account selection, permission, profile, social, engagement, messaging, or
purchase workflow.
