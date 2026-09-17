# AGNI

Routed multi-system agent harness. One LLM tool loop dispatching to six
subsystems, rebuilt on the HADES operating contract: **deterministic CLIs >
headless browser > device UI**, in-process secret handling, and hard refusal
boundaries on irreversible actions.

## Routing

| tool        | binary          | handles |
|-------------|-----------------|---------|
| `bitwarden` | `bw`            | vault status/unlock, item search |
| `github`    | `gh`            | repos, PRs, issues, actions, `gh api` |
| `gog`       | `gog`           | Gmail, Calendar, Drive, Docs, Sheets (`--account=<email>`) |
| `browser`   | `browser-use`   | rendered web automation; `BU_CDP_URL`, `BU_NAME` session isolation |
| `android`   | `adb`           | taps, swipes, text, uiautomator dump, screencap, install |
| `ios`       | `xcrun simctl`  | simulator boot/install/launch/screenshot |
| `auth`      | pipeline        | `bw` unlock → credential fetch → `browser-use` fill |

`./agni --routes` prints this table; `./agni --doctor` reports binary +
auth status per subsystem.

## Guards

Subsystem guards refuse destructive/irreversible commands before execution —
the agent gets `REFUSED: <reason>` and must escalate rather than retry.
Examples: `gh repo delete`, `gh pr merge`, `gog send`, `bw delete`,
`simctl erase`, purchases/transfers via browser, lock-screen passcodes via adb.

## Auth / login flow

```sh
agni auth github --url https://github.com/login
# or inside the agent loop: auth(action=load, site=<bw-item>) then
# browser(argv=[...], use_login_env=true)
```

1. `bw status` → unlock via `BW_SESSION` or `AGNI_BW_PASSWORD` (`--passwordenv`).
2. `bw get item <site>` is consumed **in-process** — username/password/TOTP
   land in `AGNI_LOGIN_*` env vars, never in stdout, logs, or the transcript.
3. The browser tool runs with those vars injected (`use_login_env=true`) so
   `browser-use` fill commands read them via `$AGNI_LOGIN_*` expansion.

Tool output is additionally scrubbed for session tokens, API keys, and JWTs
before it reaches the model.

## Requirements

- `gh` (authenticated), `bw`, `gog`, `browser-use`, `adb`, `xcrun simctl`
  — each optional; `--doctor` shows what's missing.
- `OPENAI_API_KEY` (or `AGNI_API_KEY`); `AGNI_MODEL`, `AGNI_BASE_URL`,
  `AGNI_MAX_TURNS` optional.

## Usage

```sh
./agni "check my github notifications and summarize today's calendar"
./agni "log into example.com and screenshot the dashboard"
./agni auth <bitwarden-item> [--url <login_url>]
./agni --dry-run "triage unread gmail"   # print tool calls, don't execute
```
