# Cast All The Things (catt) User Guide

The `catt` adapter enables discovering local Chromecast devices, casting video or audio URLs, and controlling playback.

## Common Operations

### 1. Discover Devices
```bash
# Scan local Wi-Fi / network for Cast devices
catt scan
```

### 2. Cast Media
```bash
# Cast YouTube or direct video URL to target device
catt -d "Living Room TV" cast "<video_url>"

# Cast local media file
catt -d "Living Room TV" cast /path/to/video.mp4
```

### 3. Playback Controls
```bash
# View active playback status
catt -d "Living Room TV" status

# Pause playback
catt -d "Living Room TV" pause

# Resume playback
catt -d "Living Room TV" play

# Stop casting
catt -d "Living Room TV" stop

# Adjust volume (0-100)
catt -d "Living Room TV" volume 50
```
