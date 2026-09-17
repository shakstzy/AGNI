---
name: android
description: Android device and emulator control via ADB and UIAutomator — taps, typing, swipes, dumps, screenshots, APK install, plus the auth2fa 2FA emulator.
---

# Android Skill

Device/emulator control. `adb`, `sdkmanager`, `avdmanager`, `emulator` are
installed; `ANDROID_SDK_ROOT=/opt/homebrew/share/android-commandlinetools`.

## Devices

- Physical devices / emulators: `adb devices`; pass `-s <serial>` when >1.
- **`auth2fa` emulator**: dedicated AVD (Android 34, pixel_6) for 2FA apps —
  see `auth` skill. This VM lacks Hypervisor.framework: always boot with
  `-feature -HVF -accel off` (TCG). Headless: `-no-window -no-audio -gpu
  swiftshader_indirect`.

## Control (raw adb)

```bash
adb shell input tap <x> <y>
adb shell input swipe <x1> <y1> <x2> <y2> [ms]
adb shell input text 'hello'
adb shell input keyevent ENTER|BACK|HOME
adb shell uiautomator dump /sdcard/ui.xml && adb pull /sdcard/ui.xml
adb exec-out screencap -p > /tmp/android.png
adb install app.apk
adb shell pm list packages | grep <name>
adb shell am start -n <pkg>/<activity>
```

## Helper CLIs (ported from HADES)

`cli/android.mjs`, `cli/coordinator.mjs`, `cli/vision.mjs` — selector-based
taps, guarded swipes, OCR/vision localization:

```bash
node cli/android.mjs tap --text 'Continue'
node cli/android.mjs type --text 'hello'
<secret-cmd> | node cli/android.mjs type-stdin   # sensitive input
node cli/android.mjs dump | screenshot --out /tmp/android.png
```

3rd-party app workflows: `adapters/<app>/ADAPTER.md`.

## Boundaries

- Batch multi-step UI traversal into deterministic CLI passes — no
  turn-by-turn LLM micro-tap loops (token burn).
- Stop for 2FA approvals, passkeys, lock-screen passcodes, payments.
- Never commit screenshots, dumps, or APKs to git.
