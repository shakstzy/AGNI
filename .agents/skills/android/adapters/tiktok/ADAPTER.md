# TikTok Android Adapter

Then read the generic Android skill.

This adapter owns repeatable control of the TikTok Android app on the connected
device. Its verified package is `com.zhiliaoapp.musically`. It does not own
TikTok browser profiles, credentials, account identity, or publishing.

## Commands

Every command confirms the exact package before acting. Use `--serial` when
more than one Android device is connected:

```bash
node .agents/skills/android/adapters/tiktok/cli/tiktok.mjs check
node .agents/skills/android/adapters/tiktok/cli/tiktok.mjs inspect
node .agents/skills/android/adapters/tiktok/cli/tiktok.mjs open
node .agents/skills/android/adapters/tiktok/cli/tiktok.mjs account-status
```

`check` proves `com.zhiliaoapp.musically` is installed. `inspect` returns fresh
foreground and UIAutomator state. `open` launches TikTok, then refreshes that
state as its completion proof. `account-status` reports the observed signed-out
surface without exposing fields or credentials.

To navigate to the observed credential form without entering or submitting any
credential, use one of TikTok's current methods:

```bash
node .agents/skills/android/adapters/tiktok/cli/tiktok.mjs begin-login --method email
node .agents/skills/android/adapters/tiktok/cli/tiktok.mjs begin-login --method phone
node .agents/skills/android/adapters/tiktok/cli/tiktok.mjs begin-login --method google
node .agents/skills/android/adapters/tiktok/cli/tiktok.mjs begin-login --method facebook
node .agents/skills/android/adapters/tiktok/cli/tiktok.mjs sign-up --email creator@outerscope.xyz
```

The `begin-login` and `sign-up` commands stop at the credential field or account chooser and return an
explicit handoff state. For sign-up, inbound verification codes sent to `*@outerscope.xyz` are extracted
automatically via `gog` from `operations@outerscope.xyz`.

For an explicit visual inspection, use `screenshot`. It writes only below the
ignored Android runtime directory:

```bash
node .agents/skills/android/adapters/tiktok/cli/tiktok.mjs screenshot \
  --out .agents/skills/android/runtime/tiktok/current.png
```

The adapter rejects screenshot paths outside that directory. Refresh the UI
before every future selector tap; never reuse coordinates or text from an
earlier session.

## Adding an action contract

Add a narrow action only when Adithya requests its exact outcome. Its contract
must name observed selectors, required preflight, stop conditions, and visible
completion proof. Do not turn an observed UI path into a reusable action until
it has been verified on the current app version.

## Stop and hand off

Stop for passwords, email or phone entry, birthday entry, device unlock,
verification codes, CAPTCHA, passkey, 2FA, account selection, or final account
submission. Adithya completes that step on the device, then the adapter
re-checks visible account state.

Do not publish, post, delete, edit drafts, follow, unfollow, like, comment,
share, message, edit a profile, change privacy, or make a purchase. These need
a separate explicitly authorized action contract.

After any allowed action, re-inspect the current TikTok screen and report the
visible result. Do not infer success from a tap alone.
