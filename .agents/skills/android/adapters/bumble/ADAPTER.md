# Bumble Android Adapter


Then read the generic Android skill.

This adapter binds only the installed package `com.bumble.app`. It exposes
fresh initial-surface checks, the exact observed phone-login actions, and the
signed-in People / Discover / Liked You / Chats actions below.

## Commands

```bash
node .agents/skills/android/adapters/bumble/cli/bumble.mjs check
node .agents/skills/android/adapters/bumble/cli/bumble.mjs open
node .agents/skills/android/adapters/bumble/cli/bumble.mjs inspect
node .agents/skills/android/adapters/bumble/cli/bumble.mjs screenshot --out initial.png
node .agents/skills/android/adapters/bumble/cli/bumble.mjs begin-login --method phone
phone-json-producing-command | node .agents/skills/android/adapters/bumble/cli/bumble.mjs fill-phone
node .agents/skills/android/adapters/bumble/cli/bumble.mjs request-code --confirm request
node .agents/skills/android/adapters/bumble/cli/bumble.mjs tab --name people
node .agents/skills/android/adapters/bumble/cli/bumble.mjs cards
node .agents/skills/android/adapters/bumble/cli/bumble.mjs discover
node .agents/skills/android/adapters/bumble/cli/bumble.mjs open-card --name NAME
node .agents/skills/android/adapters/bumble/cli/bumble.mjs like --confirm like
node .agents/skills/android/adapters/bumble/cli/bumble.mjs pass --confirm pass
node .agents/skills/android/adapters/bumble/cli/bumble.mjs liked-you
node .agents/skills/android/adapters/bumble/cli/bumble.mjs chats
node .agents/skills/android/adapters/bumble/cli/bumble.mjs open-chat --name NAME
message-json-producing-command | node .agents/skills/android/adapters/bumble/cli/bumble.mjs send-message --confirm send
node .agents/skills/android/adapters/bumble/cli/bumble.mjs crawl-chats [--limit 50] [--scrolls 10]
node .agents/skills/android/adapters/bumble/cli/bumble.mjs inspect-thread --name NAME
node .agents/skills/android/adapters/bumble/cli/bumble.mjs inspect-profile --name NAME [--out path.png]
node .agents/skills/android/adapters/bumble/cli/bumble.mjs ingest [--limit 50] [--scrolls 10] [--out dir]
batch-json-producing-command | node .agents/skills/android/adapters/bumble/cli/bumble.mjs send-batch --confirm send
```

`check` confirms the package. `open` launches it and returns fresh foreground
and UI state. `inspect` returns fresh foreground and UI state. `screenshot`
writes runtime-only output below the ignored Android runtime directory.

`begin-login --method phone [--serial <device-id>]` launches the exact Bumble
package. It condition-waits first for the full exact empty phone-field anchor;
if found, it freshly proves Bumble focus and the safe form, then returns
`phone-surface-ready` without a tap. Only that field wait timing out permits
the initial route. The adapter condition-waits only for the exact observed
app-owned anchor after every route tap, then freshly proves Bumble focus, the
safe surface, and the exact control before proceeding through only this route:

1. `I have an account`, no resource ID, `View`, `[55,1702][1025,1834]`
2. `Continue with other methods`, no resource ID, `View`,
   `[55,1702][1025,1834]`
3. `Use cell phone number`, no resource ID, `View`,
   `[55,1669][1025,1801]`

It does not implement Quick sign in, Facebook, Google, or any other method.
Its result says only that the phone surface is ready and no code was requested.
`Continue with other methods` is the observed Bumble navigation control; a
visible `Continue with Google`, `Continue with Facebook`, or `Continue with
Apple` provider handoff is a stop condition after the phone route. Those labels
coexist with the exact `Use cell phone number` control on the observed method
menu, so they do not block that one exact app-owned navigation tap.

`fill-phone [--serial <device-id>]` reads exactly one JSON object from standard
input: `{ "phone": "..." }`. `phone` must be a non-empty, single-line string;
no other field is accepted. The phone is never accepted in a CLI option and is
never returned in JSON, errors, logs, or files. The command freshly proves the
exact Bumble focus and phone form, guarded-taps the phone field, passes the
phone only through child standard input to the generic Android `type-stdin`
command, and refreshes the exact form. It refuses an already populated field
and rechecks the exact safe surface after focusing the field, before typing.
It never taps Continue or requests a code.

`request-code --confirm request [--serial <device-id>]` reads no credential or
code and performs no device action without that exact confirmation. It freshly
proves the exact Bumble focus and phone form, guarded-taps only the observed
Continue button, then re-inspects. Its result says only `submission-observed`
and `authentication: unverified`; it does not claim that a code was sent or
that authentication succeeded. A changed focus, provider/account handoff, or
verification-code surface stops there; there is no code-entry action.

The exact observed phone form is:

- phone field `com.bumble.app:id/reg_input_edittext`, `EditText`,
  `[325,742][1014,869]`
- `Continue` button `com.bumble.app:id/reg_footer_button`, `Button`,
  empty text with description `Continue`. Its footer layout has appeared at
  both `[904,1039][1036,1171]` and `[904,1843][1036,1975]`; the adapter
  requires one exact, non-zero, freshly observed footprint and supplies that
  footprint to the final guarded tap.

Every mutation uses an immediately observed index, exact description or
resource ID, class, exact non-zero bounds, and `--unique true`. Every stop
pattern, including account-selection and provider prompts, is also a final
generic rejection guard. The only exception is the guarded exact `Use cell
phone number` tap, whose observed menu coexists with Google/Facebook/Apple
provider-option labels. Provider handoffs remain fresh pre/post-action stop
conditions. The generic Android command takes its own fresh dump and refuses a
missing, moved, changed, duplicate, or newly unsafe final state.

The phone actions fail closed before their next mutation when focus is not the
exact Bumble package, an observed surface or control is missing, moved,
changed, or duplicated, or a provider/account handoff, passkey/identity, 2FA,
CAPTCHA, permission, purchase, profile, or social surface is visible. Stop
there and hand control to Adithya. There is no code-entry action and no
provider, account-selection, profile-setup, or social-linking workflow.

## Signed-in engagement

Tab names are `people`, `discover`, `liked-you`, and `chats`. `tab` taps only
the bottom tab-bar control (`y1 >= 1800`) so a People-card `Liked You` badge
is not the tab. `cards` lists visible People name/age/subtitle rows. `discover`
lists recommended profile buttons (`Name, age, profile N of M`). `liked-you`
lists inbound `Check out Name’s profile` rows. `chats` lists
`connectionsItem_personName` rows with preview and badge. None of those list
commands tap SuperSwipe, Beeline, Voice call, or Video call.

`like --confirm like` taps the unique overlay `Like` control. `pass --confirm
pass` taps `Not for me`. Both require the profile overlay and never tap
`Send SuperSwipe`. `open-chat --name` taps the match row whose description
starts with that name. `send-message --confirm send` reads `{ "message": "..." }`
from stdin, types it through `type-stdin` into `chatInput_text`, then taps
`Send`. The message is never a CLI option and is never returned.

`crawl-chats [--limit 50] [--scrolls 10]` systematically scrolls through the chats list, deduplicates match rows, and returns a catalog of all discovered chats.
`inspect-thread --name NAME` opens a chat thread, extracts all messages and timestamps with sender attribution (`You` vs match name), parses any shared phone numbers, and navigates back out to the chats list.
`inspect-profile --name NAME [--out path.png]` navigates to the match's full profile, extracts biographical info, occupation, education, and prompts, and navigates back out.
`ingest [--limit 50] [--scrolls 10] [--out dir]` is the atomic zero-token batch extraction primitive. It crawls the chat list, inspects each thread and profile sequentially, and outputs complete structured JSON without intermediary LLM roundtrips.
`send-batch --confirm send` accepts a JSON array of `[{"name": "...", "message": "..."}]` via stdin, dispatches each message sequentially with deterministic keyboard entry and tap actions, and returns an execution report.

Engagement fails closed on subscribe / Bumble Boost / payment / billing,
passkeys, and permission prompts. It does not tap SuperSwipe, Voice call, or
Video call. Purchases stay out of scope.
