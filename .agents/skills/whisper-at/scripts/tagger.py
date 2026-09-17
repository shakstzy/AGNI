#!/usr/bin/env python3
"""Audio transcription and sound event detection using Whisper-AT."""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

def extract_audio_from_media(media_path: Path, output_wav: Path):
    """Extract 16kHz mono WAV from any audio or video container using ffmpeg."""
    cmd = [
        "ffmpeg", "-y", "-i", str(media_path),
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        str(output_wav)
    ]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"ffmpeg extraction failed: {res.stderr}")

def main():
    parser = argparse.ArgumentParser(description="Transcribe speech and detect sound events with Whisper-AT")
    parser.add_argument("input", help="Path to input audio or video file")
    parser.add_argument("--model", default="tiny", choices=["tiny", "base", "small", "medium", "large"], help="Whisper-AT model size")
    parser.add_argument("--device", default="cuda", help="Execution device (cuda or cpu)")
    parser.add_argument("--time-resolution", type=float, default=2.0, help="Audio event resolution in seconds (multiple of 0.4, default: 2.0)")
    parser.add_argument("--top-k", type=int, default=3, help="Top K audio event tags per interval")
    parser.add_argument("--prob-threshold", type=float, default=0.15, help="Probability threshold for audio events")
    parser.add_argument("--output", "-o", help="Optional output JSON file path")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    if not input_path.is_file():
        sys.stderr.write(f"Input file not found: {input_path}\n")
        sys.exit(1)

    import whisper_at

    with tempfile.TemporaryDirectory() as tmpdir:
        wav_path = Path(tmpdir) / "extracted.wav"
        extract_audio_from_media(input_path, wav_path)

        model = whisper_at.load_model(args.model, device=args.device)
        result = model.transcribe(str(wav_path), at_time_res=args.time_resolution)

        parsed_tags = whisper_at.parse_at_label(
            result,
            language="follow_asr",
            top_k=args.top_k,
            p_threshold=args.prob_threshold,
            include_class_list=list(range(527))
        )

    # Format speech segments
    speech_segments = []
    for seg in result.get("segments", []):
        text = seg.get("text", "").strip()
        if text:
            speech_segments.append({
                "start": round(seg.get("start", 0.0), 2),
                "end": round(seg.get("end", 0.0), 2),
                "text": text
            })

    # Format audio event tags
    audio_events = []
    for item in parsed_tags:
        time_sec = item.get("time", 0)
        events = []
        for name, prob in item.get("audio tags", []):
            events.append({
                "label": name,
                "confidence": round(float(prob), 3)
            })
        if events:
            audio_events.append({
                "time_sec": time_sec,
                "events": events
            })

    output_data = {
        "file": str(input_path),
        "duration_sec": round(result.get("segments", [{}])[-1].get("end", 0.0) if result.get("segments") else 0.0, 2),
        "full_text": result.get("text", "").strip(),
        "speech_segments": speech_segments,
        "audio_events": audio_events
    }

    formatted_json = json.dumps(output_data, indent=2)

    if args.output:
        out_file = Path(args.output).resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(formatted_json)
        print(f"Results written to {out_file}")
    else:
        print(formatted_json)

if __name__ == "__main__":
    main()
