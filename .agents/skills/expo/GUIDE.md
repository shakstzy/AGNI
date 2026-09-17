# Expo & EAS CLI User Guide

The `expo` adapter enables managing React Native applications, Expo developer servers, and EAS cloud compilation pipelines.

## Common Operations

### 1. Check Version & Auth Status
```bash
# Verify EAS authentication
eas whoami

# Check CLI versions
expo --version
eas --version
```

### 2. EAS Cloud Builds & Deployments
```bash
# List recent cloud builds
eas build:list --limit 5

# View status of active EAS project
eas project:info
```

### 3. Local Development & Bundling
```bash
# Start local Metro bundler (inside project directory)
npx expo start

# Run native prebuild generation
npx expo prebuild --clean
```

### 4. Credentials & Keystores
```bash
# Inspect configured iOS / Android build credentials
eas credentials
```
