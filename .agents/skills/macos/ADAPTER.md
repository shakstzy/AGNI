# macOS Remote Host Adapter

Technical adapter contract for interacting with Adithya's personal macOS host over pinned Tailscale SSH.

## Operating Contract

- **Binary / Entry**: `macos` in PATH (symlinked to `.agents/skills/local/macos/macos`).
- **Core Script**: `.agents/skills/local/macos/macos.py` (dependency-free Python 3).
- **Transport**: BatchMode pinned SSH into the Mac with `UserKnownHostsFile` and dedicated SSH identity key.
- **Connection Configuration**:
  - Resolved in order:
    1. Ambient environment variables (`MACOS_HOST`, `MACOS_USER`, `MACOS_KNOWN_HOSTS`, `MACOS_IDENTITY`).
    2. Externalized JSON configuration at `~/.config/hades/apple/apple-config.json` (mode `0600`).
  - Pinned host keys and private keys are strictly externalized in `~/.config/hades/apple/` (mode `0600`).
  - Zero private keys or host records stored in the git repository.

## Capabilities

1. **Host Readiness & Tooling Status**:
   - `macos status` verifies reachability and presence of developer tools (`xcodebuild`, `xcrun`, `fastlane`, `pod`, `node`, `npm`, `brew`).
2. **Xcode Remote Compilation**:
   - `macos xcodebuild ...` runs Xcode commands directly on macOS.
3. **Login Shell Command Execution**:
   - `macos exec "<cmd>"` executes arbitrary shell commands inside `zsh -l`.
4. **Tool Binary Discovery**:
   - `macos which <tool>` checks if a tool exists in the macOS environment.

## Routing & Boundaries

- **Authoritative Gateway**: Any workspace or agent needing to query, build on, or run commands on Adithya's Mac must use `macos` directly.
- **Strict Skill Isolation**: Never inspect, parse, or traverse leaf productivity tools (`apple-notes`, `apple-reminders`, `macos-contacts`) to discover Mac SSH hostnames or keys. Those adapters are consumer endpoints, not host management gateways.
