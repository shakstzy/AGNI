---
name: home-assistant
description: Home Assistant REST CLI adapter for device control, entity queries, and state management.
---

# Home Assistant Guide

Direct device control, entity queries, and configuration inspection via the Home Assistant REST API.

## Execution Pattern

Home Assistant commands run via the native `ha` CLI on PATH or directly via script:

```bash
# Natural language intent execution (auto-resolves intent, dispatches in parallel, verifies state)
ha act "turn on upstairs fan and light"
ha turn on upstairs fan and light
ha turn off kitchen and countertop
ha lower upstairs fan speed
ha raise upstairs fan speed
ha act "take snapshot of doorbell"
ha act "what's the weather"
ha act "who is home"

# Instant Camera Snapshots (<1s directly via camera_proxy endpoint)
ha snapshot doorbell
ha snapshot backyard
ha snapshot front_camera /tmp/front.jpg

# Motorized Camera PTZ & Button Press
ha ptz upstairs left
ha ptz upstairs right
ha press button.upstairs_pan_left

# Media Player Remote Control
ha pause tv
ha play tv
ha mute soundbar
ha media volume tv 50

# Light Color & Temperature
ha color corner blue
ha color lamp "#00ff88"
ha color wled warm_white

# Environmental Weather & Presence
ha weather
ha presence

# Speed & dimming adjustments (relative or target percentage)
ha speed upstairs_fan lower
ha speed upstairs_fan raise
ha speed upstairs_fan 60

# Fan preset modes (e.g. steady sleep mode vs oscillating nature/fresh breeze)
ha preset downstairs_fan sleep
ha preset downstairs_fan smart

# Multi-target parallel control (instant alias resolution + programmatic verification)
ha on upstairs_fan upstairs_fan_light
ha off kitchen living_room countertop
ha on upstairs
ha off downstairs

# Room shortcuts
ha upstairs <on|off|state>
ha downstairs <on|off|state>

# Query entity, group, or alias state (concise by default)
ha state upstairs
ha state kitchen
ha state sun.sun

# Instant device index (zero network calls, reads local ~/.config/hades/devices.json)
ha devices
ha devices --domain light
ha devices --domain camera

# Sync and refresh all Home Assistant devices into local index
ha sync

# View or bind custom nicknames
ha alias reading_light light.ceiling_fan

# Full JSON output (optional, use --json when raw attributes/context needed)
ha state upstairs --json
ha on kitchen --json
ha weather --json

# Direct service call (generic)
ha call light turn_on --entity light.kitchen --data '{"brightness_pct": 50}'
ha call light turn_off --entity light.kitchen
```

## Entity & Alias Quick Reference

| Target / Alias | Entity ID | Domain | Notes |
| :--- | :--- | :--- | :--- |
| `doorbell` | `camera.casco_doorbell_live_view` | camera | Front doorbell camera snapshot (`ha snapshot doorbell`) |
| `backyard_camera` | `camera.casco_backyard_live_view` | camera | Backyard camera snapshot (`ha snapshot backyard`) |
| `front_camera` | `camera.casco_front_live_view` | camera | Front exterior camera snapshot |
| `upstairs_camera` | `camera.upstairs_live_view` | camera | Indoor motorized PTZ camera (`ha ptz upstairs left/right`) |
| `downstairs_camera` | `camera.downstairs_live_view` | camera | Indoor motorized PTZ camera (`ha ptz downstairs up/down`) |
| `tv` / `roku` | `media_player.shaku` | media_player | Living room Roku streaming receiver (`ha pause tv`) |
| `soundbar` | `media_player.shaksurround` | media_player | Surround soundbar (`ha mute soundbar`) |
| `weather` | `weather.forecast_home` | weather | Local Austin forecast & weather conditions (`ha weather`) |
| `shak` | `person.shakestate` | person | Shak personal presence status (`ha presence`) |
| `downstairs` | `switch.living_room`, `switch.kitchen` | switch | Downstairs living & kitchen switches |
| `downstairs_fan` | `fan.fan` | fan | Downstairs ceiling fan (`ha on/off downstairs_fan`) |
| `downstairs_fan_light` | `light.fan` | light | Downstairs fan light (`ha on/off downstairs_fan_light`) |
| `upstairs` | `light.ceiling_fan`, `fan.ceiling_fan` | light/fan | Upstairs ceiling fan & light combined |
| `upstairs_fan` | `fan.ceiling_fan` | fan | Upstairs ceiling fan (`ha speed upstairs_fan 50`) |
| `upstairs_fan_light` | `light.ceiling_fan` | light | Upstairs ceiling fan light |
| `kitchen` | `switch.kitchen` | switch | Kitchen main switch |
| `living_room` | `switch.living_room` | switch | Living room main switch |
| `countertop` | `switch.countertop` | switch | Countertop switch |
| `desk` | `switch.desk_socket_1` | switch | Desk socket 1 |

## Scheduling & Automation Boundary

- For requested future or recurring device actions, route through the **`scheduler`** workspace (`workspaces/scheduler/`).
- Do not create unmanaged Home Assistant automations in the cloud UI when a user requests a schedule; keep scheduled jobs tracked locally under `workspaces/scheduler/state/jobs.json`.

## Best Practices & Security Rules

1. **Single-Turn Execution with Programmatic Verification**: Actions (`ha on`, `ha off`, `ha toggle`, `ha act`) execute concurrently and automatically poll Home Assistant until the device state is verified (`(verified)`). Do NOT run manual multi-turn pre-flight or post-flight state inspection loops.
2. **Zero Secret Exposure**: Never print or commit `HOME_ASSISTANT_TOKEN`. Tokens are redacted in output.
3. **Externalized Storage**: Host credentials live in `~/.config/hades/home-assistant.json` (mode `0600`), never tracked in repository files.
