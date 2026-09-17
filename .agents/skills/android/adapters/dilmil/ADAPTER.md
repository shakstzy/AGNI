# Dil Mil Android Adapter

Package: `co.dilmil.android`

This adapter binds the official Dil Mil Android package, providing package preflight, phone OTP authentication intake, OTP verification, and connection/match monitoring.

## Commands

```bash
# Package verification & state
node .agents/skills/android/adapters/dilmil/cli/dilmil.mjs check
node .agents/skills/android/adapters/dilmil/cli/dilmil.mjs inspect
node .agents/skills/android/adapters/dilmil/cli/dilmil.mjs open
node .agents/skills/android/adapters/dilmil/cli/dilmil.mjs screenshot --out initial.png

# Phone OTP authentication
node .agents/skills/android/adapters/dilmil/cli/dilmil.mjs begin-login --method phone
printf '{"phone":"+1XXXXXXXXXX"}\n' | node .agents/skills/android/adapters/dilmil/cli/dilmil.mjs fill-phone
printf '{"otp":"123456"}\n' | node .agents/skills/android/adapters/dilmil/cli/dilmil.mjs verify-otp --confirm verify

# Connection monitoring
node .agents/skills/android/adapters/dilmil/cli/dilmil.mjs connections
node .agents/skills/android/adapters/dilmil/cli/dilmil.mjs matches
```

## Security & Human Boundaries

1. Secrets must be passed exclusively through standard input (`stdin`). CLI arguments for sensitive tokens are strictly rejected.
2. All operations stop immediately on Google/Apple account selectors, biometrics, CAPTCHA, permissions, or Dil Mil VIP/Elite purchase surfaces.
3. Screenshots are strictly jailed within `.agents/skills/android/runtime/dilmil/`.
