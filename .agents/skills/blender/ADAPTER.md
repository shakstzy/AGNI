# Blender Local CLI Adapter

Local CLI adapter providing programmatic 3D scene inspection, object/mesh manipulation, Python execution, asset importing (Poly Haven, Poly Pizza, Sketchfab), and 3D AI generation (Hyper3D Rodin, Hunyuan3D) via BlenderMCP.

## Operating Contract

- **Binary**: `/home/shakstzy/.local/bin/blender` (standalone compiled binary via MCPorter).
- **Transport**: Stdio execution using `uvx blender-mcp`.
- **Configuration**: Managed in `~/.mcporter/mcporter.json` under server identifier `blender`.
- **Bridge Connection**: Connects to the local Blender addon TCP socket server (default `127.0.0.1:9876`).
- **Headless Pipeline**: `/usr/bin/blender` headless scene rendering and GLB export via `scripts/scene_pipeline.py` (0 GUI requirement).
- **Execution Pattern**: Standalone subcommands (`blender get-addon-status`, `blender execute-blender-code`, `blender get-scene-info`, `blender get-viewport-screenshot`, etc.) or via `mcporter call blender.<tool>`.

## Inspect First

Check configuration and live server connection:

```bash
which blender
blender --help
blender get-addon-status
```

## Security & State Boundaries

1. **No In-Repo State**: Zero credentials or runtime artifacts are stored inside `HADES`.
2. **Bridge Requirement**: Real-time scene mutations and queries require a running Blender instance with the `addon.py` enabled.
3. **Graceful Failures**: When Blender or the addon is not running, commands return clear connection error diagnostics without hanging.
