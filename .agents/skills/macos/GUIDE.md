# macOS Remote Host User Guide

The `macos` adapter manages command execution, Xcode native builds, and tool discovery on Adithya's personal MacBook Pro over pinned Tailscale SSH.

## Quick Reference

| Action | Command |
| --- | --- |
| Check host & toolchain status | `macos status` |
| Check host status (JSON) | `macos status --json` |
| Execute command on Mac | `macos exec "<command>"` |
| Check binary presence on Mac | `macos which <binary>` |
| Run Xcode build command | `macos xcodebuild [args...]` |

## Examples

### 1. Check Connectivity & Developer Toolchain
```bash
macos status
```

### 2. Check Xcode Version
```bash
macos xcodebuild -version
```

### 3. Run Remote Command in macOS Login Shell
```bash
macos exec "sw_vers && which fastlane"
```

### 4. Locate Tool Binary
```bash
macos which pod
```
