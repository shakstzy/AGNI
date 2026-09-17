# Whisper-AT Adapter

The Whisper-AT adapter extracts timestamped Automatic Speech Recognition (ASR) transcripts and 527 AudioSet sound event classifications from video or audio files.

## Operating Contract

- **Runtime**: `/home/shakstzy/comfy-venv/bin/python` (PyTorch 2.12.0+cu130)
- **Acceleration**: NVIDIA Blackwell GB10 (`cuda:0`)
- **Default Entrypoint**: `.agents/skills/local/whisper-at/scripts/whisper_tag`
- **Supported Formats**: Any audio or video container (mp4, mkv, mov, mp3, wav, flac, etc. via ffmpeg)
- **Tag Resolution**: Multiples of 0.4s (defaults to 2.0s or 10.0s)
- **Class Ontology**: 527 AudioSet classes (e.g. applause, animal sounds, vehicle noise, water splash, etc.)
