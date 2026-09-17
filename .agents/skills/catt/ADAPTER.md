# Cast All The Things (catt) Adapter

Technical adapter contract for discovering local Chromecast devices and controlling media playback via the native `catt` CLI.

## Operating Contract

- **Binary**: `/home/shakstzy/.local/bin/catt` (or ambient `catt` in PATH).
- **Execution**: Direct native CLI (`catt [-d <device>] <command> [args]`).
- **Targeting**: Specify device explicitly with `-d <device_name_or_ip>` or scan using `catt scan`.

## Safety & Boundaries

- **Playback Boundaries**:
  - Never initiate media playback on devices in shared living spaces without user request.
  - Device discovery (`catt scan`) and playback status (`catt status`) can be executed freely.
