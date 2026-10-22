#!/usr/bin/env bash
# One-time setup: Python deps + ffmpeg check + voice model download (~350 MB, cached in ~/.cache/paper-shorts).
set -e
python3 -m pip install -q kokoro-onnx soundfile numpy pillow
command -v ffmpeg >/dev/null || { echo "ffmpeg is required (apt-get install ffmpeg / brew install ffmpeg)"; exit 1; }
python3 -c "import sys; sys.path.insert(0, '$(dirname "$0")'); import tts; tts.ensure_model()"
echo "paper-explainer-shorts ready"
