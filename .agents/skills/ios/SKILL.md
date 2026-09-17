---
name: ios
description: iOS simulator control via `xcrun simctl` — devices, boot, install, launch, screenshots, and UI input.
---

# iOS Skill

Control iOS simulators through `xcrun simctl` (Xcode installed).

## Execution

```bash
xcrun simctl list devices available        # discover simulators
open -a Simulator                           # boot default device (GUI)
xcrun simctl boot <udid>                    # headless boot
xcrun simctl install booted <app>.app
xcrun simctl launch booted <bundle-id>
xcrun simctl io booted screenshot /tmp/ios.png
xcrun simctl io booted recordVideo /tmp/ios.mp4
xcrun simctl openurl booted <url>
xcrun simctl ui booted appearance dark
xcrun simctl push booted <bundle-id> <payload.json>
xcrun simctl status_bar booted override --time 9:41 --batteryState charged
```

- `booted` targets the running simulator; use a UDID when several are up.
- Coordinate taps are not in simctl — use `xcrun simctl ui`/deep links, or
  Xcode's `xctest` for UI automation; fall back to accessibility tooling
  for pixel-level input.

## Boundaries

- `simctl erase`/`shutdown all` require human approval (harness guard).
- Never commit screenshots, device dumps, or .app/.ipa artifacts to git.
