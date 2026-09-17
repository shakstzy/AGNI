# Android App Adapter Template

## Identity & Package
- **App Name**: `<App Name>`
- **Package ID**: `<com.example.app>`
- **Primary Activity**: `<com.example.app.MainActivity>`

## Launch & Verify
```bash
node .agents/skills/android/cli/android.mjs launch --package <com.example.app>
node .agents/skills/android/cli/android.mjs wait --contains '<Anchor Text>'
```

## Standard Commands & Lifecycle
```bash
# Inspection & foreground status
node .agents/skills/android/adapters/<app>/cli/<app>.mjs check
node .agents/skills/android/adapters/<app>/cli/<app>.mjs open
node .agents/skills/android/adapters/<app>/cli/<app>.mjs inspect
node .agents/skills/android/adapters/<app>/cli/<app>.mjs screenshot --out runtime.png

# Zero-Token Batch Ingestion (Autonomous on-device crawl)
node .agents/skills/android/adapters/<app>/cli/<app>.mjs ingest [--limit <n>] [--out <dir>]

# Zero-Token Batch Dispatch (Sequential mutation pass)
cat batch_actions.json | node .agents/skills/android/adapters/<app>/cli/<app>.mjs dispatch
```

## Key Selectors
- **Primary Action Button**: `--id '<package>:id/<button_id>'` or `--text '<Button Label>'`
- **Input Field**: `--id '<package>:id/<input_id>'`

## Boundaries & Verification
- **Zero-Token Rule**: Never recall LLM across intermediate taps/scrolls. Ingestion and dispatch must be 100% deterministic scripts.
- State postcondition proof required after mutations.
- Never automate passkey prompts, payments, or destructive account deletions.

