# Android App Adapters Registry

| Child | Route |
| --- | --- |
| REGISTRY.md | App-adapter routing map. |
| bumble/ | Bumble Android package, phone login, and signed-in People/Discover/Liked You/Chats actions. Read `bumble/REGISTRY.md`. |
| cli/ | Shared bounded Android app-adapter primitive. Import `cli/standard-app.mjs`. |
| dilmil/ | Dil Mil Android package, phone OTP intake, and connections. Read `dilmil/REGISTRY.md`. |
| hinge/ | Hinge Android package, navigation, profile ingest, and messaging. Read `hinge/REGISTRY.md`. |
| mirchi/ | Mirchi Android package and safe initial-surface checks. Read `mirchi/REGISTRY.md`. |
| plenty-of-fish/ | Plenty of Fish Android package, safe initial-surface checks, and bounded login fill/submit contracts. Read `plenty-of-fish/REGISTRY.md`. |
| play-store/ | Google Play Store search, free-install workflow, and releases. Read `play-store/REGISTRY.md`. |
| tests/ | Shared app-adapter contract tests. Run `node --test tests/*.test.mjs`. |
| tiktok/ | TikTok Android package, account switching, creation hooks, content staging. Read `tiktok/REGISTRY.md`. |

Use one app adapter only after the generic Android skill selects a device.
Adapters manage app automation mechanics; account profiles are managed under `profiles/` per adapter and skill.
