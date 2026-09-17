---
name: whisper-at
description: Dual speech-to-text transcription and 527-class audio event detection with timestamps.
---

# Whisper-AT Guide

Extract speech transcripts and sound events simultaneously from any media file using Whisper-AT on CUDA.

## Execution Pattern

### Direct CLI Tagging

Run on any audio or video file:

```bash
# Basic run with tiny model and 2s event resolution
.agents/skills/local/whisper-at/scripts/whisper_tag /path/to/video.mp4

# Save output directly to JSON
.agents/skills/local/whisper-at/scripts/whisper_tag /path/to/video.mp4 \
  --model base \
  --time-resolution 2.0 \
  --output metadata.json
```

### JSON Schema Output

```json
{
  "file": "/path/to/video.mp4",
  "duration_sec": 14.5,
  "full_text": "Look at the dog jumping!",
  "speech_segments": [
    {
      "start": 0.5,
      "end": 2.8,
      "text": "Look at the dog jumping!"
    }
  ],
  "audio_events": [
    {
      "time_sec": {
        "start": 2.0,
        "end": 4.0
      },
      "events": [
        {
          "label": "Bark",
          "confidence": 0.421
        },
        {
          "label": "Splash",
          "confidence": 0.312
        }
      ]
    }
  ]
}
```
