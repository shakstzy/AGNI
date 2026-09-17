# AGNI

A root-level agent harness that wires the **GitHub CLI** (`gh`) and the
**browser-use CLI** (`browser-use`) into a single LLM tool loop.

The agent gets exactly two tools:

| tool      | executes                | use for |
|-----------|-------------------------|---------|
| `github`  | `gh <argv...>`          | repos, PRs, issues, `gh api`, `gh search` |
| `browser` | `browser-use <argv...>` | rendering pages, clicking through UIs, screenshots, forms |

Everything lives at the repository root — one executable, no package layout.

## Requirements

- `gh` — GitHub CLI, authenticated (`gh auth login`)
- `browser-use` — [browser-use](https://github.com/browser-use/browser-use) CLI
  (`pip install browser-use`, or point `PATH` at `uvx browser-use`)
- An OpenAI-compatible API key

## Setup

```sh
export OPENAI_API_KEY=sk-...          # or AGNI_API_KEY
./agni --doctor                        # verify gh + browser-use are wired
```

Optional env:

- `AGNI_MODEL` — model name (default `gpt-4o`)
- `AGNI_BASE_URL` — OpenAI-compatible base URL (default `https://api.openai.com/v1`)
- `AGNI_MAX_TURNS` — tool-loop cap (default `25`)

## Usage

```sh
./agni "list my open PRs and open the repo page in the browser"
./agni "create an issue on shakstzy/AGNI titled 'bootstrap' and confirm it renders"
./agni --dry-run "triage notifications"   # see the tool calls without executing
```

The harness prints every underlying `gh` / `browser-use` invocation as it runs,
then the agent's final summary.
