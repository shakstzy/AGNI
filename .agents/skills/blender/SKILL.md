---
name: blender
description: Programmatic 3D scene inspection, object/mesh manipulation, Python execution, asset importing, and AI generation using BlenderMCP through MCPorter.
---

# Blender Guide

Use the `blender` CLI to inspect active 3D scenes, execute Blender Python scripts (`bpy`), capture viewport screenshots, import assets, and generate 3D models.

## Execution Patterns

```bash
# Verify connection to Blender addon
blender get-addon-status

# Inspect scene hierarchy, active objects, cameras, and lights
blender get-scene-info

# Inspect specific object properties
blender get-object-info --name "Cube"

# Capture viewport screenshot
blender get-viewport-screenshot

# Execute custom Blender Python code
blender execute-blender-code --code "import bpy; bpy.ops.mesh.primitive_cube_add(location=(0, 0, 2))"

# Search and download Poly Haven assets (HDRI, textures, models)
blender search-polyhaven-assets --asset-type models
blender download-polyhaven-asset --asset-id "wooden_table" --asset-type models

# Search and download Poly Pizza models
blender search-polypizza-models --query "chair" --licence CC0
blender download-polypizza-model --model-id "<id>"

# Search and download Sketchfab models
blender search-sketchfab-models --query "sports car"
blender download-sketchfab-model --model-uid "<uid>"

# Generate 3D models with Hunyuan3D or Hyper3D Rodin
blender generate-hunyuan3d-model --text-prompt "futuristic helmet"
blender generate-hyper3d-model-via-text --text-prompt "medieval shield"

# Direct MCPorter invocation
mcporter call blender.get_scene_info
```

## Autonomous Scene Pipeline (Description to 3D Scene)

For autonomous 3D scene generation from text descriptions with minimal token overhead, use the headless pipeline in `scripts/scene_pipeline.py`:

```bash
# 1. Initialize scene workspace and boilerplate (cameras, lighting rig, AgX tonemapping, ground plane)
python3 .agents/skills/local/blender/scripts/scene_pipeline.py init --dir .3d-scenes/cyberpunk-alley

# 2. Render viewport preview, save .blend, and export .glb
python3 .agents/skills/local/blender/scripts/scene_pipeline.py render \
  --script .3d-scenes/cyberpunk-alley/scene.py \
  --out-img .3d-scenes/cyberpunk-alley/render_round_1.png \
  --out-blend .3d-scenes/cyberpunk-alley/scene.blend \
  --out-glb .3d-scenes/cyberpunk-alley/scene.glb

# 3. Inspect scene hierarchy (concise JSON: objects, lights, vertices, materials)
python3 .agents/skills/local/blender/scripts/scene_pipeline.py inspect \
  --script .3d-scenes/cyberpunk-alley/scene.py

# 4. Generate token-minimal prompt for subagent critic
python3 .agents/skills/local/blender/scripts/scene_pipeline.py critic-prompt \
  --concept .3d-scenes/cyberpunk-alley/concept.png \
  --render .3d-scenes/cyberpunk-alley/render_round_1.png \
  --round 1
```

### Token-Optimized Dream-Loop Architecture

| Step | Role | Execution | Input Tokens | Cost |
|---|---|---|---|---|
| **0. Visual Anchor** | Image Model | `generate_image` (AAA in-engine concept) | ~100 | Built-in |
| **1. Scene Blueprint** | Builder LLM | Generate `scene.py` from boilerplate | ~3,500 | ~$0.005 |
| **2. Fast Render** | Headless Blender | `scene_pipeline.py render` (2.5s) | 0 | Free |
| **3. Stateless Critic** | Subagent (`flash`) | 5-tier gated rubric on 2 images | ~2,500 | <$0.0005 |
| **4. Delta Fix** | Builder LLM | Apply critic's 3 blockers to `scene.py` | ~3,500 | ~$0.005 |
| **Convergence** | ≤ 3 rounds max | Exit when `score >= 7.5` | ~18k total | **< $0.02** |

## Setup & Addon Installation

To connect to a live interactive Blender workspace:
1. Ensure Blender is installed and running.
2. Install the bundled addon if not already installed:
   ```bash
   uvx blender-mcp install-addon
   ```
3. In Blender, enable the addon under **Edit > Preferences > Add-ons > Blender MCP**.

