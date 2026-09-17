# Plenty of Fish Android Adapter


Then read the generic Android skill.

This adapter binds only the installed package `com.pof.android`. It exposes
fresh initial-surface checks plus the separately bounded login-fill and
login-submit contracts documented below.

## Commands

```bash
node .agents/skills/android/adapters/plenty-of-fish/cli/plenty-of-fish.mjs check
node .agents/skills/android/adapters/plenty-of-fish/cli/plenty-of-fish.mjs open
node .agents/skills/android/adapters/plenty-of-fish/cli/plenty-of-fish.mjs inspect
node .agents/skills/android/adapters/plenty-of-fish/cli/plenty-of-fish.mjs screenshot --out initial.png
credential-producing-command | node .agents/skills/android/adapters/plenty-of-fish/cli/plenty-of-fish.mjs fill-login
node .agents/skills/android/adapters/plenty-of-fish/cli/plenty-of-fish.mjs submit-login --confirm submit
```

`check` confirms the exact package. `open` launches it and returns fresh
foreground and UI state. `inspect` returns fresh foreground and UI state.
`screenshot` writes runtime-only output below the ignored Android runtime
directory.

`fill-login [--serial <device-id>]` reads exactly one JSON object from standard
input with exactly two non-empty, single-line string fields: `username` and
`password`. Credentials are never options and are never returned in JSON,
errors, logs, or files. The command verifies the exact POF package, launches
only that package, and condition-waits for the exact observed username control.
It then freshly confirms foreground focus, a safe surface, and unique observed
login controls before each field tap. It taps only `com.pof.android:id/username` and
`com.pof.android:id/password`, invokes the generic Android `type-stdin` command
separately for each value through child standard input, and re-inspects after
every mutation. It does not tap Log in.

Each login-control tap is guarded twice. The adapter derives the control's
array position, exact resource ID, exact class, and non-zero bounds from its
immediately preceding fresh dump and sends all four constraints plus
`--unique true` to the generic Android tap. The generic command refreshes the
UI again and refuses the tap if any part of that fingerprint changed or is no
longer unique. It also receives every unsafe-authentication pattern through
`--reject-regex`, so a provider, permission, identity, verification, CAPTCHA,
purchase, profile, or social-linking surface that appears in that final refresh
stops the tap.
A refusal stops the adapter before typing or post-submit work.

`submit-login --confirm submit [--serial <device-id>]` accepts no credentials.
Without that exact confirmation it performs no device action. It freshly
proves the exact visible POF login form and safe foreground state, taps only
`com.pof.android:id/login`, then freshly re-proves exact POF focus and rejects
every unsafe authentication surface, including code entry. Its redacted result
says only that submission was observed and authentication remains unverified;
it never claims sign-in success.

The observed exact login controls are:

- `com.pof.android:id/username`, `android.widget.EditText`, label `Username or email`
- `com.pof.android:id/password`, `android.widget.EditText`, label `Password`
- `com.pof.android:id/login`, `android.widget.Button`, label `Log in`

The authentication commands fail closed before mutation if focus is not the
exact POF package, a control is missing, duplicated, or changed, or an account
selection/owner, permission, passkey/identity, 2FA, CAPTCHA, purchase, profile,
or social-linking surface is visible. Stop there and hand control to Adithya. This
adapter still implements no account selection, profile creation or editing,
messaging, engagement, or purchases.
