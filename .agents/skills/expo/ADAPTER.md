# Expo & EAS CLI Adapter

Technical adapter contract for managing React Native mobile applications, native prebuilds, and Expo Application Services (EAS) cloud builds via `expo` and `eas`.

## Operating Contract

- **Binaries**: `/home/shakstzy/.local/bin/expo` and `/home/shakstzy/.local/bin/eas`.
- **Execution**: Direct native CLI (`expo <command> [flags]`, `eas <command> [flags]`).
- **Context Targeting**:
  - Run within mobile project root or target with `--project-dir <path>`.
  - Used in coordination with `workspaces/app-builder`.
- **Runtime Credentials**:
  - Managed via `eas login` with session stored in `~/.eas/`.
  - Zero Apple Developer or Google Play keystore secrets committed to git.

## Safety & Boundaries

- **Secret Exposure Guard**:
  - Never print or commit mobile keystores, provisioning profiles, or EAS secret tokens.
- **Approval Boundaries**:
  - Ask for explicit approval before submitting apps to app stores (`eas submit --platform all`).
  - Ask for explicit approval before running production builds that consume paid EAS cloud build credits (`eas build --platform all --profile production`).
  - Read-only inspections (`eas whoami`, `eas build:list`, `expo --version`, `eas project:info`) can be executed freely.
