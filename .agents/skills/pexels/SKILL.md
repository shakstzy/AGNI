---
name: pexels
description: The pexels adapter searches and downloads high-resolution stock photography and B-roll video directly from the Pexels API.
---

# Pexels Stock Media CLI User Guide

The `pexels` adapter searches and downloads high-resolution stock photography and B-roll video directly from the Pexels API.

## Authentication

API keys are loaded in priority order:
1. `PEXELS_API_KEY` in environment
2. `PEXELS_API_KEY` in `/home/shakstzy/HADES/.env`
3. Bitwarden item `pexels.com (adithya@outerscope.xyz)`

## Common Operations

### 1. Search Stock Photos
```bash
# Search photos with terminal summary
pexels search "robotics manipulator" --count 5

# Search with orientation filter (landscape, portrait, square)
pexels search "server rack data center" --count 3 --orientation landscape

# Output raw JSON
pexels search "gpu compute" --count 2 --json
```

### 2. Search & Download Photos Directly
```bash
# Download top 3 images to asset directory with prefix
pexels download "industrial robotics" -o ./assets/robotics/ --count 3 --prefix "robot"

# Download specific size (original, large2x, large, medium, small)
pexels download "circuit board" -o ./assets/hardware/ --size large2x
```

### 3. Python API Integration
```python
from workspaces.socials.pexels import search_photos, search_and_download

# Search photos
photos = search_photos("robot arm", count=3, orientation="landscape")

# Download directly
saved = search_and_download("server cluster", dest_dir="./assets", count=2, prefix="compute")
```
