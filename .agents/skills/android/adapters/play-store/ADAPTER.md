# Google Play Store Android Adapter

Before interaction, read `../../SKILL.md`.

Package: `com.android.vending`

The adapter owns exact-package checks, opening and inspecting Google Play Store,
searching for app listings, enumerating bounded matching result cards, and
starting an observed free installation.
It refreshes UI evidence before selector taps and after mutations.

`candidates` returns matching result cards in observed order with zero-based
`resultIndex`, exact title, selector field, and non-zero bounds. Cards at
different bounds remain distinct; geometry-identical accessibility duplicates
collapse. Discovery fails closed unless the complete bounded Play Store search
header is freshly observed with consistent `Navigate up`, `Search Google Play`,
and `Voice Search` anchors.

`install-free` requires `--result-index` when more than one distinct candidate
is visible and never chooses among them implicitly. It refuses out-of-range
indexes, prices or purchase prompts, missing exact `Install` controls, account
prompts, and permission prompts. Detail, preflight, and install-state evidence
must retain the selected candidate's exact title. It stops after visible
install progress or completion evidence. It never accepts purchases, sign-ins,
permissions, subscriptions, or external state ownership.

Use:

```bash
node cli/play-store.mjs check [--serial SERIAL]
node cli/play-store.mjs open [--serial SERIAL]
node cli/play-store.mjs inspect [--serial SERIAL]
node cli/play-store.mjs search --query "APP" [--serial SERIAL]
node cli/play-store.mjs candidates --query "APP" [--serial SERIAL]
node cli/play-store.mjs install-free --query "APP" [--result-index N] [--serial SERIAL]
```
